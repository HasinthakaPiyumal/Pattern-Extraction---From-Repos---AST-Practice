// Cluster 5

// Node: builder
// Node: build
// Node: info
// Node: title
// Node: description
// Node: assertNotNull
// Node: isEmpty
// Node: getTitle
// Node: getDescription
package com.itachallenge.githubcore.service;

import com.itachallenge.githubcore.document.enums.GithubUserStatus;
import com.itachallenge.githubcore.exception.GithubUnavailableException;
import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import org.junit.jupiter.api.*;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.test.StepVerifier;

import java.io.IOException;

class GithubApiServiceImplTest {

    private static MockWebServer mockWebServer;
    private GithubApiServiceImpl githubApiServiceImpl;

    @BeforeAll
    static void startServer() throws IOException {
        mockWebServer = new MockWebServer();
        mockWebServer.start();

    }

    @AfterAll
    static void shutdownServer() throws IOException {
        mockWebServer.shutdown();
    }

    @BeforeEach
    void setup() {
        String mockBaseUrl = mockWebServer.url("/").toString();
        githubApiServiceImpl = new GithubApiServiceImpl(WebClient.builder(), mockBaseUrl);
    }

    @Test
    void exists_ShouldReturnTrue_WhenResponseIs200() {
        mockWebServer.enqueue(new MockResponse()
                .setResponseCode(200)
                .setBody("{\"login\":\"testUser\"}")
                .addHeader("Content-Type", "application/json"));

        StepVerifier.create(githubApiServiceImpl.userExists("testUser"))
                .expectNext(GithubUserStatus.FOUND)
                .verifyComplete();
    }

    @Test
    void exists_ShouldReturnFalse_WhenResponseIs404() {
        mockWebServer.enqueue(new MockResponse()
                .setResponseCode(404)
                .setBody("{\"message\":\"Not Found\"}")
                .addHeader("Content-Type", "application/json"));

        StepVerifier.create(githubApiServiceImpl.userExists("testuser19"))
                .expectNext(GithubUserStatus.NOT_FOUND)
                .verifyComplete();
    }

    @Test
    void exists_ShouldReturnFalse_WhenResponseIs500() {
        mockWebServer.enqueue(new MockResponse()
                .setResponseCode(500)
                .setBody("{\"message\":\"Server Error\"}")
                .addHeader("Content-Type", "application/json"));

        StepVerifier.create(githubApiServiceImpl.userExists("unknownuser"))
                .expectError(GithubUnavailableException.class)
                .verify();
    }


}

// Node: url
// Node: map
// Node: toList
package com.itachallenge.errorcore.builder;


import com.fasterxml.jackson.databind.exc.InvalidFormatException;
import com.itachallenge.errorcore.dto.APIErrorResponse;
import com.itachallenge.errorcore.dto.FieldErrorDto;
import com.itachallenge.errorcore.exception.BaseApiException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.ConstraintViolation;
import jakarta.validation.ConstraintViolationException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.MessageSource;
import org.springframework.context.i18n.LocaleContextHolder;
import org.springframework.core.codec.DecodingException;
import org.springframework.http.HttpStatus;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.web.server.ServerWebInputException;

import java.util.List;
import java.util.Locale;

@Slf4j
@RequiredArgsConstructor
public class ErrorResponseBuilder {

    private final MessageSource messageSource;

    /** Build general error response.*/
    public APIErrorResponse buildError(
            Exception e,
            HttpServletRequest request
    ) {
        ExceptionMapping mapping = mapException(e);
        return APIErrorResponse.builder()
                .status(mapping.status.value())
                .error(mapping.status.getReasonPhrase())
                .message(resolveMessage(mapping.messageKey))
                .path(request != null ? request.getRequestURI() : null)
                .build();
    }

    public APIErrorResponse buildCustomExceptionError(
            BaseApiException e,
            HttpServletRequest request
    ) {
        ExceptionMapping mapping = mapException(e);
        return APIErrorResponse.builder()
                .status(mapping.status.value())
                .error(mapping.status.getReasonPhrase())
                .message(resolveMessage(mapping.messageKey,e.getInfo().messageArgs()))
                .path(request != null ? request.getRequestURI() : null)
                .build();
    }

    public APIErrorResponse buildArgumentNotValidErrorResponse(MethodArgumentNotValidException ex, HttpServletRequest request) {
        String objectName = ex.getBindingResult().getObjectName();
        return buildValidationErrorResponse(
                resolveMessage(mapException(ex).messageKey,objectName),
                extractFieldErrors(ex),
                request
        );
    }

    public APIErrorResponse buildConstraintViolationErrorResponse(ConstraintViolationException ex, HttpServletRequest request) {
        return buildValidationErrorResponse(
                resolveMessage(mapException(ex).messageKey),
                extractConstraintViolations(ex),
                request
        );
    }

    public APIErrorResponse buildTypeMismatchErrorResponse(MethodArgumentTypeMismatchException ex, HttpServletRequest request) {
        return buildValidationErrorResponse(
                resolveMessage(
                        mapException(ex).messageKey,
                        ex.getName(),                                   // {0} parameter name
                        ex.getValue(),                                  // {1} invalid value
                        ex.getRequiredType() != null
                                ? ex.getRequiredType().getSimpleName()
                                : "unknown"                                 // {2} expected type
                ),
                singleFieldErrorList(ex),
                request
        );
    }

    public APIErrorResponse buildStatusErrorResponse(ResponseStatusException ex, HttpServletRequest request) {
        HttpStatusCode statusCode = ex.getStatusCode();
        String errorMessage = resolveMessage(mapException(ex).messageKey);
        // Build the APIErrorResponse using your builder (same message text)
        return APIErrorResponse.builder()
                .status(statusCode.value())
                .error(ex.getReason())
                .message(errorMessage)
                .path(request != null ? request.getRequestURI() : null)
                .build();
    }

    // --- PRIVATE HELPERS ----------------------------------------------------
    /** Converts a validation violation into a detailed field error DTO. */
    private FieldErrorDto toFieldErrorDto(ConstraintViolation<?> violation) {
        String fieldName = extractFieldName(violation);
        String detailedMessage = resolveMessage(
                "validation.constraint.detailed",
                fieldName,
                violation.getMessage()
        );
        return FieldErrorDto.builder()
                .objectName(violation.getRootBeanClass().getSimpleName())
                .field(fieldName)
                .message(detailedMessage)
                .build();
    }

    /** Extracts field-level errors from @Valid annotated DTOs. */
    private List<FieldErrorDto> extractFieldErrors(MethodArgumentNotValidException ex) {
        Locale locale = LocaleContextHolder.getLocale();
        return ex.getBindingResult()
                .getFieldErrors()
                .stream()
                .map(error -> FieldErrorDto.builder()
                        .objectName(error.getObjectName())
                        .field(error.getField())
                        .message(messageSource.getMessage(error, locale))
                        .build())
                .toList();
    }

    /** Extracts constraint violations from @Validated annotated method parameters. */
    private List<FieldErrorDto> extractConstraintViolations(ConstraintViolationException ex) {
        return ex.getConstraintViolations()
                .stream()
                .map(this::toFieldErrorDto)
                .toList();
    }

    /** Creates a singleton list of FieldErrorDto for type mismatch or single-parameter errors. */
    private List<FieldErrorDto> singleFieldErrorList(MethodArgumentTypeMismatchException ex) {
        String field = ex.getName();
        String rejectedValue = ex.getValue() != null ? ex.getValue().toString() : "null";
        String requiredType = ex.getRequiredType() != null ? ex.getRequiredType().getSimpleName() : "unknown";

        FieldErrorDto fieldError = FieldErrorDto.builder()
                .objectName(ex.getParameter().getContainingClass().getSimpleName())
                .field(field)
                .message(resolveMessage(mapException(ex).messageKey,
                        field,
                        rejectedValue,
                        requiredType)
                )
                .build();

        return List.of(fieldError);
    }

    /** Extracts the last segment of the property path (the field name). */
    private String extractFieldName(ConstraintViolation<?> violation) {
        return violation.getPropertyPath().toString()
                .replaceAll("^.*\\.", ""); // e.g., user.email -> email
    }

    /** Build validation error response.*/
    private APIErrorResponse buildValidationErrorResponse(
            String message,
            List<FieldErrorDto> fieldErrors,
            HttpServletRequest request
    ) {
        return APIErrorResponse.builder()
                .status(HttpStatus.BAD_REQUEST.value())
                .error(HttpStatus.BAD_REQUEST.getReasonPhrase())
                .message(message)
                .errors(fieldErrors)
                .path(request != null ? request.getRequestURI() : null)
                .build();
    }

    /** Resolve message from message source. */
    public String resolveMessage(String messageKey) {
        return resolveMessage(messageKey, new Object[]{});
    }
    private String resolveMessage(String messageKey, Object arg1) {
        return resolveMessage(messageKey, new Object[]{arg1});
    }
    private String resolveMessage(String messageKey, Object arg1, Object arg2) {
        return resolveMessage(messageKey, new Object[]{arg1, arg2});
    }
    private String resolveMessage(String messageKey, Object arg1, Object arg2, Object arg3) {
        return resolveMessage(messageKey, new Object[]{arg1, arg2, arg3});
    }
    private String resolveMessage(String messageKey, Object[] args) {
        Locale locale = LocaleContextHolder.getLocale();
        try {
            return messageSource.getMessage(messageKey, args, locale);
        } catch (Exception e) {
            log.debug("No message found for key '{}', using literal", messageKey);
            return messageKey; // fallback to literal if no translation found
        }
    }

    // --- Exception Mapping----------------------------------------------------

    /** Internal record representing the mapping of an exception to a message key and HTTP status. */
    private record ExceptionMapping(HttpStatus status, String messageKey) {}

    /** Determines the appropriate message key and HTTP status for a given exception. */
    private ExceptionMapping mapException(Exception e) {
        // --- Validation & argument errors ---
        if (e instanceof BaseApiException bae)
            return new ExceptionMapping(bae.getInfo().status(), bae.getInfo().messageKey());

        if (e instanceof MethodArgumentNotValidException)
            return new ExceptionMapping(HttpStatus.BAD_REQUEST, "validation.argument_not_valid");

        if (e instanceof ConstraintViolationException)
            return new ExceptionMapping(HttpStatus.BAD_REQUEST, "validation.constraint");

        if (e instanceof MethodArgumentTypeMismatchException)
            return new ExceptionMapping(HttpStatus.BAD_REQUEST, "validation.type_mismatch");

        if (e instanceof IllegalArgumentException)
            return new ExceptionMapping(HttpStatus.BAD_REQUEST, "validation.illegal_argument");

        if (e instanceof InvalidFormatException
                || e instanceof HttpMessageNotReadableException
                || e instanceof ServerWebInputException
                || e instanceof DecodingException)
            return new ExceptionMapping(HttpStatus.BAD_REQUEST, "validation.bad_request");

        // --- ResponseStatusException (explicit HTTP semantics) ---
        if (e instanceof ResponseStatusException rse)
            return new ExceptionMapping(HttpStatus.valueOf(rse.getStatusCode().value()),
                    "status.exception." + rse.getStatusCode().value());
        // --- Default / fallback case ---
        log.warn("Unhandled exception type in ErrorResponseBuilder: {}", e.getClass().getName());
        return new ExceptionMapping(HttpStatus.INTERNAL_SERVER_ERROR, "internal.server_error");
    }

}


// Node: valueOf
// Node: validate
package com.itachallenge.errorcore.exceptionhandler;

import com.fasterxml.jackson.databind.exc.InvalidFormatException;
import com.itachallenge.errorcore.builder.ErrorResponseBuilder;
import com.itachallenge.errorcore.dto.APIErrorResponse;
import com.itachallenge.errorcore.exception.ApiCustomErrorInfo;
import com.itachallenge.errorcore.exception.BaseApiException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.ConstraintViolationException;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.HttpInputMessage;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.mock.http.MockHttpInputMessage;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.web.server.ServerWebInputException;

import java.util.Set;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class GlobalExceptionHandlerUnitTest {

    @Mock
    private ErrorResponseBuilder builder;

    @Mock
    private HttpServletRequest request;

    @InjectMocks
    private GlobalExceptionHandler handler;

    private final APIErrorResponse dummyResponse = APIErrorResponse.builder()
            .status(400)
            .error("Bad Request")
            .message("dummy")
            .build();


    @Test
    void handleAny_shouldReturnInternalServerError() {
        when(builder.buildError(any(Exception.class),eq(request)))
                .thenReturn(dummyResponse);

        ResponseEntity<APIErrorResponse> response = handler.handleAny(new Exception("boom"), request);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.INTERNAL_SERVER_ERROR);
        verify(builder).buildError(any(Exception.class), eq(request));
    }

    @Test
    void handleIllegalArgument_shouldReturnBadRequest() {
        when(builder.buildError(any(IllegalArgumentException.class), eq(request)))
                .thenReturn(dummyResponse);

        ResponseEntity<APIErrorResponse> response = handler.handleIllegalArgument(
                new IllegalArgumentException("invalid input"), request);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        verify(builder).buildError(any(IllegalArgumentException.class), eq(request));
    }

    @Test
    void handleValidationExceptions_shouldDelegateToBuilder() {
        ConstraintViolationException ex = new ConstraintViolationException(Set.of());
        when(builder.buildConstraintViolationErrorResponse(ex, request)).thenReturn(dummyResponse);

        ResponseEntity<APIErrorResponse> response = handler.handleValidationExceptions(ex, request);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        verify(builder).buildConstraintViolationErrorResponse(ex, request);
    }

    @Test
    void handleTypeMismatchException_shouldDelegateToBuilder() {
        MethodArgumentTypeMismatchException ex = mock(MethodArgumentTypeMismatchException.class);
        when(builder.buildTypeMismatchErrorResponse(ex, request)).thenReturn(dummyResponse);

        ResponseEntity<APIErrorResponse> response = handler.handleTypeMismatchException(ex, request);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        verify(builder).buildTypeMismatchErrorResponse(ex, request);
    }

    @Test
    void handleMethodArgumentNotValidException_shouldDelegateToBuilder() {
        MethodArgumentNotValidException ex = mock(MethodArgumentNotValidException.class);
        when(builder.buildArgumentNotValidErrorResponse(ex, request)).thenReturn(dummyResponse);

        ResponseEntity<APIErrorResponse> response = handler.handleMethodArgumentNotValidException(ex, request);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        verify(builder).buildArgumentNotValidErrorResponse(ex, request);
    }

    @Test
    void handleResponseStatusException_shouldUseStatusFromException() {
        ResponseStatusException ex = new ResponseStatusException(HttpStatus.NOT_FOUND, "Not found");
        when(builder.buildStatusErrorResponse(ex, request)).thenReturn(dummyResponse);

        ResponseEntity<APIErrorResponse> response = handler.handleResponseStatusException(ex, request);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.NOT_FOUND);
        verify(builder).buildStatusErrorResponse(ex, request);
    }

    @Test
    void handleInvalidFormat_shouldReturnBadRequestAndDelegateToBuilder() {
        InvalidFormatException ex = mock(InvalidFormatException.class);
        when(builder.buildError(ex, request))
                .thenReturn(dummyResponse);

        ResponseEntity<APIErrorResponse> response = handler.handleInvalidFormat(ex, request);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        assertThat(response.getBody()).isEqualTo(dummyResponse);
        verify(builder).buildError(ex, request);
    }

    @Test
    void handleWebFluxBindingErrors_withInvalidFormatCause_shouldDelegateToHandleInvalidFormat() {
        InvalidFormatException rootCause = mock(InvalidFormatException.class);
        HttpInputMessage mockInput = new MockHttpInputMessage("{}".getBytes());
        HttpMessageNotReadableException ex =
                new HttpMessageNotReadableException("invalid", rootCause, mockInput);
        when(builder.buildError(rootCause, request))
                .thenReturn(dummyResponse);

        ResponseEntity<APIErrorResponse> response = handler.handleWebFluxBindingErrors(ex, request);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        verify(builder).buildError(rootCause, request);
    }

    @Test
    void handleWebFluxBindingErrors_withoutInvalidFormatCause_shouldReturnGenericBadRequest() {
        ServerWebInputException ex = new ServerWebInputException("Bad JSON");
        when(builder.buildError(ex, request))
                .thenReturn(dummyResponse);
        ResponseEntity<APIErrorResponse> response = handler.handleWebFluxBindingErrors(ex, request);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        verify(builder).buildError(ex, request);
    }
    @Test
    void handleCustomError_shouldDelegateAndToCustomBuildAndReturnExceptionStatusCode(){

        class GenericNotFoundException extends BaseApiException {
            GenericNotFoundException(String arg){
                super(arg, ApiCustomErrorInfo.of(HttpStatus.NOT_FOUND,"error.notFound",new Object[]{arg}));
            }
        }
        GenericNotFoundException ex = new GenericNotFoundException("GenericNotFound");
        when (builder.buildCustomExceptionError(ex,request))
                .thenReturn(dummyResponse);

        ResponseEntity<APIErrorResponse> response = handler.handleApiCustomException(ex, request);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.NOT_FOUND);
        verify(builder).buildCustomExceptionError(ex,request);
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/error-response-core/src/test/java/com/itachallenge/errorcore/exceptionhandler/GlobalExceptionHandlerUnitTest.java:GlobalExceptionHandlerUnitTest.<init>
// Node: flatMap
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


// Node: zip
// Node: getT1
// Node: getT2
// Node: switchIfEmpty
// Node: save
// Node: deleteFromFavorites
// Node: then
package com.itachallenge.user.exception;

public class InternalServerErrorException extends RuntimeException {

    public InternalServerErrorException(String message) {
        super(message);
    }

}

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/exception/InternalServerErrorException.java:InternalServerErrorException.<init>
// Node: InternalServerErrorException
// Node: getRole
package com.itachallenge.user.controller;

import com.itachallenge.user.annotations.ValidGithubUsername;
import com.itachallenge.user.document.UserDocument;
import com.itachallenge.user.dto.SubmitSolutionResponseDto;
import com.itachallenge.user.dto.UserSolutionRequestDto;
import com.itachallenge.user.service.IUserSolutionService;
import com.itachallenge.user.service.UserService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.enums.ParameterIn;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import jakarta.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.ErrorResponse;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

@RestController
@Validated
@RequestMapping(value = "/itachallenge/api/v1/user")
public class UserController {

    private static final Logger log = LoggerFactory.getLogger(UserController.class);
    public static final String X_VALIDATION_STATUS = "X-Validation-Status";
    public static final String X_GITHUB_USERNAME ="X-Github-Username";

    private final UserService userService;
    private final IUserSolutionService userSolutionService;

    public UserController(UserService userService, IUserSolutionService userSolutionService) {
        this.userService = userService;
        this.userSolutionService = userSolutionService;
    }

    @GetMapping(value = "/test")
    public String test() {
        return "Hello from ITA Challenge UserController!!!";
    }

    @Operation(
            summary = "Retrieve User",
            description = "Retrieves user details for the given GitHub username if it exists in the database.",
            parameters = {
                    @Parameter(
                            name = "githubUsername",
                            description = "GitHub username to search in the database.",
                            required = true,
                            in = ParameterIn.PATH
                    )
            },
            responses = {
                    @ApiResponse(
                            responseCode = "200",
                            description = "User retrieved successfully",
                            content = @Content(mediaType = "application/json", schema = @Schema(implementation = UserDocument.class))
                    ),
                    @ApiResponse(
                            responseCode = "400",
                            description = "Invalid request. The provided Github username is not valid.",
                            content = @Content(mediaType = "application/json")
                    ),
                    @ApiResponse(
                            responseCode = "404",
                            description = "User not found. The requested Github username does not exist in the database",
                            content = @Content(mediaType = "application/json")
                    ),
                    @ApiResponse(
                            responseCode = "500",
                            description = "Internal server error. An unexpected error occurred while retrieving the user.",
                            content = @Content(mediaType = "application/json")
                    )
            }
    )

    @GetMapping("/users/{githubUsername}")
    public Mono<ResponseEntity<UserDocument>> getUser(@PathVariable @ValidGithubUsername String githubUsername) {
        return userService.getUser(githubUsername)
                .map(user -> {
                    log.info("User found: {} (Role: {})", githubUsername, user.getRole());
                    return ResponseEntity.ok()
                            .header(X_VALIDATION_STATUS, "Success")
                            .header(X_GITHUB_USERNAME, githubUsername)
                            .body(user);
                });
    }

    @PutMapping(path = "/solution")
    @Operation(
            summary = "Submit a solution using action-based workflow",
            description = "Perform solution submission using actions (SAVE, GIVE_UP, SUBMIT) instead of direct status updates",
            responses = {
                    @ApiResponse(responseCode = "200", description = "Solution successfully processed",
                            content = {@Content(schema = @Schema(implementation = UserSolutionRequestDto.class),
                                    mediaType = "application/json")}),
                    @ApiResponse(responseCode = "400", description = "Invalid action or bad request",
                            content = {@Content(schema = @Schema())}),
                    @ApiResponse(
                            responseCode = "409", description = "Solution already submitted and cannot be modified",
                            content = @Content(schema = @Schema(implementation = ErrorResponse.class), mediaType = "application/json")),
                    @ApiResponse(responseCode = "500", description = "Internal server error",
                            content = @Content(schema = @Schema(implementation = ErrorResponse.class), mediaType = "application/json"))
            }
    )
    public Mono<ResponseEntity<SubmitSolutionResponseDto>> addSolution(
            @Valid @RequestBody UserSolutionRequestDto userSolutionDto) {

        return userSolutionService.addSolution(userSolutionDto)
                .map(savedUserSolutionDto ->
                        ResponseEntity.status(HttpStatus.OK).body(savedUserSolutionDto)
                );
    }

    @Operation(
            summary = "Add Challenge to User Bookmark Challenges",
            description = "Adds challenge to user Bookmarks",
            parameters = {
                    @Parameter(
                            name = "userId",
                            description = "User ID",
                            required = true,
                            in = ParameterIn.PATH
                    ),
                    @Parameter(
                            name = "challengeId",
                            description = "Challenge ID",
                            required = true,
                            in = ParameterIn.PATH
                    )
            },
            responses = {
                    @ApiResponse(
                            responseCode = "200",
                            description = "Challenge is already in bookmarks",
                            content = @Content(mediaType = "application/json")
                    ),
                    @ApiResponse(
                            responseCode = "201",
                            description = "Challenge added to bookmarks",
                            content = @Content(mediaType = "application/json")
                    ),
                    @ApiResponse(
                            responseCode = "400",
                            description = "Bad Request. The provided IDs have a bad format",
                            content = @Content(mediaType = "application/json")
                    ),
                    @ApiResponse(
                            responseCode = "404",
                            description = "Not found. No user is found with the provided user id.",
                            content = @Content(mediaType = "application/json")
                    ),
                    @ApiResponse(
                            responseCode = "500",
                            description = "Internal server error. An unexpected error occurred.",
                            content = @Content(mediaType = "application/json")
                    )
            }
    )

    @PostMapping("/users/{userId}/bookmarks/{challengeId}")
    public Mono<ResponseEntity<Boolean>> addToBookmarks(@PathVariable String userId, @PathVariable String challengeId) {
        return userService.addChallengeToBookmarks(userId, challengeId)
                .map(added -> {
                    if (Boolean.TRUE.equals(added)) {
                        log.info("Challenge '{}' added to user '{}' bookmarks", challengeId, userId);
                        return ResponseEntity.status(HttpStatus.CREATED).body(true);
                    } else {
                        log.info("User's '{}' bookmarks already contain Challenge '{}'", userId, challengeId);
                        return ResponseEntity.ok().body(false);
                    }
                });
    }

    @Operation(
            summary = "Delete Challenge from User Bookmark Challenges",
            description = "Deletes challenge from user bookmarks",
            parameters = {
                    @Parameter(
                            name = "userId",
                            description = "User ID",
                            required = true,
                            in = ParameterIn.PATH
                    ),
                    @Parameter(
                            name = "challengeId",
                            description = "Challenge ID",
                            required = true,
                            in = ParameterIn.PATH
                    )
            },
            responses = {
                    @ApiResponse(
                            responseCode = "200",
                            description = "Challenge deleted from bookmarks or was not in bookmarks",
                            content = @Content(mediaType = "application/json")
                    ),
                    @ApiResponse(
                            responseCode = "400",
                            description = "Bad Request. The provided IDs have a bad format",
                            content = @Content(mediaType = "application/json")
                    ),
                    @ApiResponse(
                            responseCode = "404",
                            description = "Not found. No user is found with the provided user id.",
                            content = @Content(mediaType = "application/json")
                    ),
                    @ApiResponse(
                            responseCode = "500",
                            description = "Internal server error. An unexpected error occurred.",
                            content = @Content(mediaType = "application/json")
                    )
            }
    )
    @DeleteMapping("/users/{userId}/bookmarks/{challengeId}")
    public Mono<ResponseEntity<Boolean>> deleteFromBookmarks(@PathVariable String userId, @PathVariable String challengeId) {
        return userService.deleteChallengeFromBookmarks(userId, challengeId)
                .map(deleted -> {
                    if (Boolean.TRUE.equals(deleted)) {
                        log.info("Challenge '{}' deleted from user '{}' bookmarks", challengeId, userId);
                        return ResponseEntity.ok().body(true);
                    } else {
                        log.info("No change, User's '{}' bookmarks doesn't contain Challenge '{}'", userId, challengeId);
                        return ResponseEntity.ok().body(false);
                    }
                });
    }

}


// Node: deleteFromBookmarks
package com.itachallenge.user.controller.userinteraction.bookmark;

import com.itachallenge.userinteraction.service.bookmark.BookmarkService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.enums.ParameterIn;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

import java.util.Set;
import java.util.UUID;

@RestController
@RequestMapping("/itachallenge/api/v1/users/{userId}/bookmarks")
public class BookmarkController {

    private static final Logger log = LoggerFactory.getLogger(BookmarkController.class);

    private final BookmarkService bookmarkService;

    public BookmarkController(BookmarkService bookmarkService) {
        this.bookmarkService = bookmarkService;
    }

    @Operation(
            summary = "Gets challenges marked as bookmarks by a user",
            description = "Returns all challenges that the specified user has marked as bookmark.",
            parameters = {
                    @Parameter(
                            name = "userId",
                            description = "UUID of the user",
                            required = true,
                            in = ParameterIn.PATH
                    )
            },
            responses = {
                    @ApiResponse(responseCode = "200", description = "Set of bookmark challengeIds by user"),
                    @ApiResponse(responseCode = "404", description = "User not found"),
                    @ApiResponse(responseCode = "400", description = "The provided IDs are not valid."),
                    @ApiResponse(responseCode = "500", description = "Unexpected error")
            }
    )

    @GetMapping
    public Mono<ResponseEntity<Set<UUID>>> getUserBookmarks(@PathVariable String userId) {
        return bookmarkService.getUserBookmarks(userId)
                .map(bookmarks -> {
                    log.info("Retrieved {} bookmark challenges for user {}", bookmarks.size(), userId);
                    return ResponseEntity.ok(bookmarks);
                });
    }
}

// Node: size
package com.itachallenge.user.controller.userinteraction.favorite;

import com.itachallenge.userinteraction.service.favorite.FavoriteService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.enums.ParameterIn;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

import java.util.Set;
import java.util.UUID;

// TODO [TECH-DEBT][Taiga-#938]:
// Refactor endpoint structure to treat favorites as a user subresource
// and remove duplicated path segments. See Taiga task for details.

@RestController
@RequestMapping("/itachallenge/api/v1/userinteraction/favorites")
public class FavoriteController {

    private static final Logger log = LoggerFactory.getLogger(FavoriteController.class);

    private final FavoriteService favoriteService;

    public FavoriteController(FavoriteService favoriteService) {
        this.favoriteService = favoriteService;
    }

    @Operation(
            summary = "Add Challenge to User Favorite Challenges",
            description = "Adds challenge to user favorites",
            parameters = {
                    @Parameter(
                            name = "userId",
                            description = "User ID",
                            required = true,
                            in = ParameterIn.PATH
                    ),
                    @Parameter(
                            name = "challengeId",
                            description = "Challenge ID",
                            required = true,
                            in = ParameterIn.PATH
                    )
            },
            responses = {
                    @ApiResponse(
                            responseCode = "200",
                            description = "Challenge is already in favorites",
                            content = @Content(mediaType = "application/json")
                    ),
                    @ApiResponse(
                            responseCode = "201",
                            description = "Challenge added to favorites",
                            content = @Content(mediaType = "application/json")
                    ),
                    @ApiResponse(
                            responseCode = "400",
                            description = "Bad Request. The provided IDs have a bad format",
                            content = @Content(mediaType = "application/json")
                    ),
                    @ApiResponse(
                            responseCode = "404",
                            description = "Not found. No user is found with the provided user id.",
                            content = @Content(mediaType = "application/json")
                    ),
                    @ApiResponse(
                            responseCode = "500",
                            description = "Internal server error. An unexpected error occurred.",
                            content = @Content(mediaType = "application/json")
                    )
            }
    )

    @PostMapping("/users/{userId}/favorites/{challengeId}")
    public Mono<ResponseEntity<Boolean>> addToFavorites(@PathVariable String userId, @PathVariable String challengeId) {
        return favoriteService.addChallengeToFavorites(userId, challengeId)
                .map(added -> {
                    if (Boolean.TRUE.equals(added)) {
                        log.info("Challenge '{}' added to user '{}' favorites", challengeId, userId);
                        return ResponseEntity.status(HttpStatus.CREATED).body(true);
                    } else {
                        log.info("User's '{}' favorites already contain Challenge '{}'", userId, challengeId);
                        return ResponseEntity.ok().body(false);
                    }
                });
    }

    @Operation(
            summary = "Gets challenges marked as favorites by a user",
            description = "Returns all favorites that the specified user has marked.",
            parameters = {
                    @Parameter(
                            name = "userId",
                            description = "UUID of the user",
                            required = true,
                            in = ParameterIn.PATH
                    )
            },
            responses = {
                    @ApiResponse(responseCode = "200", description = "Set of favorite challengeIds by user"),
                    @ApiResponse(responseCode = "404", description = "User not found"),
                    @ApiResponse(responseCode = "400", description = "The provided IDs are not valid."),
                    @ApiResponse(responseCode = "500", description = "Unexpected error")
            }
    )
    @GetMapping("/{userId}")
    public Mono<ResponseEntity<Set<UUID>>> getUserFavorites(@PathVariable String userId) {
        return favoriteService.getUserFavorites(userId)
                .map(favorites -> {
                    log.info("Retrieved {} favorite challenges for user {}", favorites.size(), userId);
                    return ResponseEntity.ok(favorites);
                });
    }

    @Operation(
            summary = "Delete Challenge from User Favorite Challenges",
            description = "Deletes challenge from user favorites",
            parameters = {
                    @Parameter(
                            name = "userId",
                            description = "User ID",
                            required = true,
                            in = ParameterIn.PATH
                    ),
                    @Parameter(
                            name = "challengeId",
                            description = "Challenge ID",
                            required = true,
                            in = ParameterIn.PATH
                    )
            },
            responses = {
                    @ApiResponse(
                            responseCode = "200",
                            description = "Challenge deleted from favorites or was not in favorites",
                            content = @Content(mediaType = "application/json")
                    ),
                    @ApiResponse(
                            responseCode = "400",
                            description = "Bad Request. The provided IDs have a bad format",
                            content = @Content(mediaType = "application/json")
                    ),
                    @ApiResponse(
                            responseCode = "404",
                            description = "Not found. No user is found with the provided user id.",
                            content = @Content(mediaType = "application/json")
                    ),
                    @ApiResponse(
                            responseCode = "500",
                            description = "Internal server error. An unexpected error occurred.",
                            content = @Content(mediaType = "application/json")
                    )
            }
    )
    @DeleteMapping("/users/{userId}/favorites/{challengeId}")
    public Mono<ResponseEntity<Boolean>> deleteFromFavorites(@PathVariable String userId, @PathVariable String challengeId) {
        return favoriteService.deleteChallengeFromFavorites(userId, challengeId)
                .map(deleted -> {
                    if (Boolean.TRUE.equals(deleted)) {
                        log.info("Challenge '{}' deleted from user '{}' favorites", challengeId, userId);
                        return ResponseEntity.ok().body(true);
                    } else {
                        log.info("No change, User's '{}' favorites doesn't contain Challenge '{}'", userId, challengeId);
                        return ResponseEntity.ok().body(false);
                    }
                });
    }
}


// Node: doOnSuccess
// Node: doOnError
package com.itachallenge.user.service;

import com.itachallenge.githubcore.exception.GithubUnavailableException;
import com.itachallenge.user.document.UserDocument;
import com.itachallenge.user.document.enums.Role;
import com.itachallenge.user.dto.AdminCreateUserRequestDto;
import com.itachallenge.user.dto.AdminCreateUserResponseDto;
import com.itachallenge.user.exception.NotFoundException;
import com.itachallenge.user.exception.UsernameAlreadyExistsException;
import com.itachallenge.user.repository.UserRepository;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.util.UUID;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Service
public class AdminCreateUserService implements IAdminCreateUserService {

    private static final Logger log = LoggerFactory.getLogger(AdminCreateUserService.class);

    private final UserRepository userRepository;
    private final ExternalGithubService externalGithubService;

    public AdminCreateUserService(UserRepository userRepository, ExternalGithubService externalGithubService) {
        this.userRepository = userRepository;
        this.externalGithubService = externalGithubService;
    }

    @Override
    public Mono<AdminCreateUserResponseDto> createUser(AdminCreateUserRequestDto request) {
        final String username = request.getUsername();
        log.info("Attempting to create user with username: {}", username);

        return userRepository.findByUsername(username)
                .flatMap(existing -> {
                    log.warn("Attempt to create a user that already exists: {}", username);
                    return Mono.<AdminCreateUserResponseDto>error(new UsernameAlreadyExistsException(username));
                })
                .switchIfEmpty(Mono.defer(() ->
                        externalGithubService.userExists(username)
                                .timeout(Duration.ofSeconds(3))
                                .onErrorMap(throwable -> {
                                    if (throwable instanceof java.util.concurrent.TimeoutException) {
                                        return new GithubUnavailableException("timeout");
                                    } else {
                                        return new GithubUnavailableException(throwable.getMessage());
                                    }
                                })
                                .flatMap(exists -> {
                                    if (Boolean.FALSE.equals(exists)) {
                                        log.warn("GitHub user '{}' does not exist", username);
                                        return Mono.error(new NotFoundException("GitHub user not found: " + username));
                                    }

                                    UserDocument newUser = UserDocument.builder()
                                            .uuid(UUID.randomUUID())
                                            .username(username)
                                            .role(Role.USER)
                                            .build();

                                    return userRepository.save(newUser)
                                            .map(savedUser -> AdminCreateUserResponseDto.builder()
                                                    .userId(savedUser.getUuid().toString())
                                                    .username(savedUser.getUsername())
                                                    .role(savedUser.getRole().toString())
                                                    .build())
                                            .doOnSuccess(responseDto ->
                                                    log.info("Successfully created user '{}'", responseDto.getUsername()));
                                })
                ));
    }
}


// Node: getUsername
// Node: timeout
// Node: username
// Node: role
// Node: getUuid
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


// Node: contentType
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

// Node: webClientBuilder
// Node: toArray
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




// Node: noArgsBuilder_test
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


// Node: points
// Node: userDocumentCreation
// Node: getPoints
// Node: settersAndGetters
// Node: setRole
// Node: setPoints
// Node: builderPattern
// Node: noArgsConstructor
// Node: assertNull
// Node: allArgsConstructor
// Node: builderHandlesNullValues
// Node: settersHandleNullValues
// Node: builderHandlesOnlyUuid
// Node: builderHandlesOnlyUsername
// Node: builderHandlesOnlyRole
// Node: builderHandlesOnlyPoints
// Node: builderCreatesNewInstances
// Node: assertNotSame
// Node: builderWithoutParametersCreatesValidObject
// Node: modifyingBuiltObjectDoesNotAffectOriginalBuilder
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




// Node: format
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

// Node: createUser_shouldAssignDefaultUserRole
// Node: anyMatch
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

// Node: flatMapMany
package com.itachallenge.challenge.exception;

public class ChallengeNotFoundException extends RuntimeException {

    public ChallengeNotFoundException(String message) {
        super(message);
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/exception/ChallengeNotFoundException.java:ChallengeNotFoundException.<init>
// Node: ChallengeNotFoundException
package com.itachallenge.challenge.exception;

public class LanguageNotFoundException extends RuntimeException {

    public LanguageNotFoundException(String message) {
        super(message);
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/exception/LanguageNotFoundException.java:LanguageNotFoundException.<init>
// Node: LanguageNotFoundException
package com.itachallenge.challenge.exception;

public class InternalServerErrorException extends RuntimeException {
    public InternalServerErrorException(String message) {
        super(message);
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/exception/InternalServerErrorException.java:InternalServerErrorException.<init>
package com.itachallenge.challenge.exception;

public class TagNotFoundException extends RuntimeException {
    public TagNotFoundException(String message) {
        super(message);
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/exception/TagNotFoundException.java:TagNotFoundException.<init>
// Node: TagNotFoundException
package com.itachallenge.challenge.controller;

import com.itachallenge.challenge.dto.GenericResultDto;
import com.itachallenge.challenge.dto.LanguageDto;
import com.itachallenge.challenge.service.ILanguageService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Mono;

@RestController
@Validated
@RequiredArgsConstructor
@RequestMapping(value = "/itachallenge/api/v1/languages")
public class LanguageController {

    @NonNull
    private ILanguageService ILanguageService;

    @GetMapping("/")
    @Operation(
            operationId = "Get all the stored languages into the Database.",
            summary = "Get to see all id language and name.",
            description = "Requesting all the languages through the URI from the database.",
            responses = {
                    @ApiResponse(responseCode = "200", content = {@Content(schema = @Schema(implementation = GenericResultDto.class), mediaType = "application/json")}),
            }
    )
    public Mono<GenericResultDto<LanguageDto>> getAllLanguages() {
        return ILanguageService.getAllLanguages();
    }
}


// Node: getAllLanguages
package com.itachallenge.challenge.controller;

import com.itachallenge.challenge.dto.GenericResultDto;
import com.itachallenge.challenge.dto.TagDto;
import com.itachallenge.challenge.service.ITagService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Mono;

import java.util.UUID;

@RestController
@Validated
@RequiredArgsConstructor
@RequestMapping(value = "/itachallenge/api/v1/tags")
public class TagController {

    private final ITagService tagService;

    @GetMapping("/{languageId}")
    @Operation(
            operationId = "Get tags by languageId",
            summary = "Get all tags filtered by languageId.",
            description = "Retrieve all tags that match the specified languageId.",
            responses = {
                    @ApiResponse(responseCode = "200", content = {@Content(schema = @Schema(implementation = GenericResultDto.class), mediaType = "application/json")}),
                    @ApiResponse(responseCode = "404", description = "No tags found for the specified languageId."),
                    @ApiResponse(responseCode = "400", description = "Malformed or invalid parameter(s)."),
                    @ApiResponse(responseCode = "500", description = "Internal Server Error")
            }
    )
    public Mono<ResponseEntity<GenericResultDto<TagDto>>> getTagsByLanguageId(@PathVariable UUID languageId) {
        return tagService.getTagsByLanguageId(languageId)
                .map(ResponseEntity::ok)
                .switchIfEmpty(Mono.just(ResponseEntity.status(HttpStatus.NOT_FOUND).build()))
                .onErrorResume(e -> Mono.just(ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build()));
    }
}


// Node: onErrorResume
// Node: createResource
// Node: ofNullable
// Node: addChallenge
// Node: findFirstByLanguageName
package com.itachallenge.challenge.document;

import com.itachallenge.challenge.enums.Topic;
import lombok.*;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
import org.springframework.data.mongodb.core.mapping.Field;

import java.time.LocalDateTime;
import java.util.*;

@Document(collection="challenges")
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ChallengeDocument {

    @Id
    @Field("_id")
    private UUID uuid;

    @Field(name = "challenge_title")
    private String title;

    @Field(name = "level")
    private String level;   //valor seteado fom properties

    @Field(name = "creation_date")
    private LocalDateTime creationDate;

    @Field(name = "detail")
    private DetailDocument detail;

    @Field(name = "languages")
    private Set<LanguageDocument> languages;

    @Field(name = "solutions")
    private List<UUID> solutions;

    @Field(name = "topic")
    private Topic topic;

    @Field(name = "times_favorite")
    private Integer timesFavorite;

    @Field(name="times_bookmark")
    private Integer timesBookmark;

    @Field(name="times_solved")
    private Integer timesSolved;

    @Field(name = "tags")
    private List<UUID> tags;

    public void increaseTimesFavorite () {
            timesFavorite = timesFavorite == null ? 1 : timesFavorite + 1;
        }

        public void decreaseTimesFavorite () {
            timesFavorite = Integer.max(timesFavorite == null ? 0 : timesFavorite - 1, 0);

        }

    public void increaseTimesBookmark() {
        timesBookmark = timesBookmark == null ? 1 : timesBookmark + 1;
    }

    public void decreaseTimesBookmark() {
        timesBookmark =Integer.max(timesBookmark == null ? 0 : timesBookmark - 1, 0);
    }
  
    public void increaseTimesSolved() {
        timesSolved = timesSolved == null ? 1 : timesSolved + 1;
    }


}


// Node: increaseTimesFavorite
// Node: decreaseTimesFavorite
// Node: max
// Node: increaseTimesBookmark
// Node: decreaseTimesBookmark
// Node: increaseTimesSolved
package com.itachallenge.challenge.service;

import com.itachallenge.challenge.document.LanguageDocument;
import com.itachallenge.challenge.dto.GenericResultDto;
import com.itachallenge.challenge.dto.LanguageDto;
import com.itachallenge.challenge.helper.DocumentToDtoConverter;
import com.itachallenge.challenge.repository.LanguageRepository;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.UUID;

@Service
@RequiredArgsConstructor
public class LanguageServiceImpl implements ILanguageService {

    private static final String LANGUAGE_NOT_FOUND = "Language with id %s not found";

    private final DocumentToDtoConverter<LanguageDocument, LanguageDto> languageConverter = new DocumentToDtoConverter<>();

    @NonNull
    private final LanguageRepository languageRepository;

    @Cacheable(value = "allLanguages")
    @Override
    public Mono<GenericResultDto<LanguageDto>> getAllLanguages() {
        Flux<LanguageDto> languagesDto = languageConverter.convertDocumentFluxToDtoFlux(languageRepository.findAll(), LanguageDto.class);
        return languagesDto.collectList().map(language -> {
            GenericResultDto<LanguageDto> resultDto = new GenericResultDto<>();
            resultDto.setInfo(0, language.size(), language.size(), language.toArray(new LanguageDto[0]));
            return resultDto;
        });
    }

    @Override
    public Mono<LanguageDocument> findByIdLanguage(UUID id){
        return languageRepository.findByIdLanguage(id);
    }

    @Override
    public Mono<LanguageDocument> findFirstByLanguageName(String languageName) {
        return languageRepository.findFirstByLanguageName(languageName);
    }

}

// Node: collectList
// Node: getChallengesByTopic
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

// Node: validateUUID
// Node: convertDocumentToDto
// Node: buildFilterPredicate
// Node: take
// Node: getAndProcessChallenges
// Node: flux
// Node: and
// Node: shuffle
// Node: apply
// Node: from
// Node: findField
// Node: getLanguage
// Node: fromDisplayName
// Node: getTopic
// Node: getSolution
// Node: idLanguage
// Node: getValidatedTags
// Node: topic
// Node: tags
// Node: subscribe
// Node: results
// Node: total
// Node: defaultIfEmpty
// Node: buildSolutionDocument
package com.itachallenge.challenge.service;

import com.itachallenge.challenge.document.ChallengeDocument;
import com.itachallenge.challenge.document.LanguageDocument;
import com.itachallenge.challenge.dto.GenericResultDto;
import com.itachallenge.challenge.dto.LanguageDto;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.Optional;
import java.util.UUID;

public interface ILanguageService {

    Mono<GenericResultDto<LanguageDto>> getAllLanguages();
    Mono<LanguageDocument> findByIdLanguage(UUID id);
    Mono<LanguageDocument> findFirstByLanguageName(String languageName);



}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/service/ILanguageService.java:ILanguageService.<init>
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

// Node: getTimesFavorite
package com.itachallenge.challenge.service;

import com.itachallenge.challenge.dto.*;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.UUID;


public interface IResourceService {
    Mono<ResourceDto> createResource(ResourceDto resourceDto);

    Flux<ResourceDto> getResourcesByChallengeId(UUID challengeId);
}



// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/service/IResourceService.java:IResourceService.<init>
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


// Node: validateNoDuplicatesUUIDTags
// Node: validateAllUUIDTagsExist
package com.itachallenge.challenge.service;
import com.itachallenge.challenge.document.ResourceDocument;
import com.itachallenge.challenge.dto.ChallengeDto;
import com.itachallenge.challenge.dto.ChallengeListDto;
import com.itachallenge.challenge.dto.ResourceDto;
import com.itachallenge.challenge.enums.AssociationType;
import com.itachallenge.challenge.enums.Topic;
import com.itachallenge.common.exception.BadRequestException;
import com.itachallenge.challenge.exception.InternalServerErrorException;
import com.itachallenge.challenge.exception.ResourceNotFoundException;
import com.itachallenge.challenge.helper.DocumentToDtoConverter;
import com.itachallenge.challenge.repository.ResourceRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.*;

@Service
public class ResourceServiceImpl implements IResourceService {
    private static final Logger log = LoggerFactory.getLogger(ResourceServiceImpl.class);
    private final ResourceRepository resourceRepository;
    private final DocumentToDtoConverter<ResourceDocument, ResourceDto> resourceConverter;
    private final IChallengeService challengeService;

    public ResourceServiceImpl(ResourceRepository resourceRepository, DocumentToDtoConverter<ResourceDocument,
            ResourceDto> resourceConverter, IChallengeService challengeService) {
        this.resourceRepository = resourceRepository;
        this.resourceConverter = resourceConverter;
        this.challengeService = challengeService;

    }

    @CacheEvict(value = "resources", allEntries = true)
    @Override
    public Mono<ResourceDto> createResource(ResourceDto resourceDto) {
        if (resourceDto == null) {
            return Mono.error(new IllegalArgumentException("ResourceDto cannot be null"));
        }
        if (resourceDto.getContentType() == null) {
            return Mono.error(new IllegalArgumentException("Content type is required"));
        }
        if (resourceDto.getTopic() == null) {
            return Mono.error(new IllegalArgumentException("Topic is required"));
        }

        Topic topic = Topic.fromDisplayName(resourceDto.getTopic().toString());
        resourceDto.setTopic(topic);

        if (resourceDto.getAssociationType() == AssociationType.NONE) {
            return saveResource(resourceDto);
        }

        if (resourceDto.getAssociationType() == AssociationType.CHOOSE) {
            return challengeService.getChallengesByTopic(topic, 0, -1)
                    .defaultIfEmpty(new ChallengeListDto(Collections.emptyList(), 0))
                    .doOnNext(challengeList -> log.info("ChallengeListDo received {}", challengeList))
                    .flatMap(challengeResult -> {
                        List<ChallengeDto> matchingChallenges = challengeResult.getResults() != null
                                ? challengeResult.getResults()
                                : new ArrayList<>();

                        if (matchingChallenges.isEmpty()) {
                            return Mono.error(new IllegalArgumentException("No challenges found for the selected topic"));
                        }

                        return Mono.just(ResourceDto.builder()
                                .resourceId(resourceDto.getResourceId())
                                .title(resourceDto.getTitle())
                                .description(resourceDto.getDescription())
                                .url(resourceDto.getUrl())
                                .topic(resourceDto.getTopic())
                                .contentType(resourceDto.getContentType())
                                .associationType(resourceDto.getAssociationType())
                                .challengeIds(matchingChallenges.stream()
                                        .map(ChallengeDto::getChallengeId)
                                        .toList())
                                .build());
                    });
        }


        return Optional.ofNullable(challengeService.getChallengesByTopic(topic, 0, -1))
                .orElse(Mono.just(new ChallengeListDto(Collections.emptyList(), 0)))
                .doOnNext(challengeList -> log.info("ChallengeListDto received {}", challengeList))
                .flatMap(challengeResult -> {
                    List<ChallengeDto> matchingChallenges = challengeResult.getResults() != null
                            ? challengeResult.getResults()
                            : new ArrayList<>();

                    if (!matchingChallenges.isEmpty()) {
                        resourceDto.setChallengeIds(matchingChallenges.stream()
                                .map(ChallengeDto::getChallengeId)
                                .toList());
                    }
                    return saveResource(resourceDto);
                })
                .switchIfEmpty(saveResource(resourceDto))
                .doOnError(error -> log.error("Error creating resource {}", error.getMessage()))
                .onErrorResume(error -> {
                    log.error("Handling error {}", error.getMessage());
                    return Mono.error(new RuntimeException("Error creating resource"));
                });
    }


    private Mono<ResourceDto> saveResource(ResourceDto resourceDto) {
        if (resourceDto == null) {
            log.error("Error where resourceDto null!");
            return Mono.error(new IllegalArgumentException("ResourceDto cannot be null"));
        }

        log.info("Trying to convert {}", resourceDto);

        ResourceDocument resourceDocument = resourceConverter.convertDtoToDocument(resourceDto, ResourceDocument.class);

        if (resourceDocument == null) {
            log.error("Error: resourceConverter is null");
            return Mono.error(new IllegalStateException("Conversion DTO to Document null"));
        }

        if (resourceDocument.getResourceId() == null) {
            resourceDocument.setResourceId(UUID.randomUUID());
        }

        resourceDocument.setContentType(resourceDto.getContentType());
        resourceDocument.setChallengeIds(resourceDto.getChallengeIds());

        return resourceRepository.save(resourceDocument)
                .map(savedResource -> {
                    ResourceDto savedDto = resourceConverter.convertDocumentToDto(savedResource, ResourceDto.class);
                    log.info("Resource created with an ID {}", savedDto.getResourceId());
                    return savedDto;
                })
                .doOnError(error -> log.error("Error occurred when creating resource {}", error.getMessage()));
    }


    public Flux<ResourceDto> getResourcesByChallengeId(UUID challengeId) {
        return Mono.justOrEmpty(challengeId)
                .switchIfEmpty(Mono.error(new BadRequestException("Challenge ID cannot be null")))
                .flatMapMany(validChallengeId ->
                        resourceRepository.findByChallengeIdsContaining(validChallengeId)
                                .map(resourceDoc -> resourceConverter.convertDocumentToDto(resourceDoc, ResourceDto.class))
                                .onErrorResume(error -> {
                                    log.error("Error fetching resources for challenge ID {}: {}", validChallengeId, error.getMessage());
                                    if (error instanceof ResourceNotFoundException) {
                                        return Flux.error(error);
                                    }
                                    return Flux.error(new InternalServerErrorException("Failed to fetch resources for challenge ID: " + validChallengeId));
                                })
                );
    }
}

// Node: getContentType
// Node: getAssociationType
// Node: saveResource
// Node: ChallengeListDto
// Node: emptyList
// Node: resourceId
// Node: getResourceId
// Node: getUrl
// Node: associationType
// Node: challengeIds
// Node: setChallengeIds
// Node: convertDtoToDocument
// Node: setContentType
// Node: getChallengeIds
package com.itachallenge.challenge.helper;

import com.itachallenge.challenge.document.ChallengeDocument;
import com.itachallenge.challenge.document.LanguageDocument;
import com.itachallenge.challenge.document.ResourceDocument;
import com.itachallenge.challenge.document.TagDocument;
import com.itachallenge.challenge.dto.ChallengeDto;
import com.itachallenge.challenge.dto.LanguageDto;
import com.itachallenge.challenge.dto.ResourceDto;
import com.itachallenge.challenge.dto.TagDto;
import org.modelmapper.AbstractConverter;
import org.modelmapper.Converter;
import org.modelmapper.ModelMapper;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.stereotype.Component;
import reactor.core.publisher.Flux;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

@Configuration
@Component
public class DocumentToDtoConverter<S,D> {

    @Bean
    public ModelMapper modelMapper() {
        return new ModelMapper();
    }

    public Flux<D> convertDocumentFluxToDtoFlux(Flux<S> documentFlux, Class<D> dtoClass) {
        return documentFlux.map(doc -> convertDocumentToDto(doc, dtoClass));
    }

    static final DateTimeFormatter CUSTOM_FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd");

    public S convertDtoToDocument(D dto, Class<S> documentClass) {
        ModelMapper mapper = new ModelMapper();
        return mapper.map(dto, documentClass);
    }

    public D convertDocumentToDto(S document, Class<D> dtoClass){
        ModelMapper mapper = new ModelMapper();

        if(dtoClass.isAssignableFrom(ChallengeDto.class)) {
            Converter<LocalDateTime, String> converterFromLocalDateTimeToString = new AbstractConverter<>() {
                @Override
                protected String convert(LocalDateTime creationDateFromDocument) {
                    return creationDateFromDocument.format(CUSTOM_FORMATTER);
                }
            };
            mapper.createTypeMap(ChallengeDocument.class, ChallengeDto.class)
                    .addMapping(ChallengeDocument::getUuid, ChallengeDto::setChallengeId)
                    .addMapping(ChallengeDocument::getTitle, ChallengeDto::setTitle)
                    .addMapping(ChallengeDocument::getTimesFavorite, ChallengeDto::setTimesFavorite)
                    .addMapping(ChallengeDocument::getTags, ChallengeDto::setTags)
                    .addMapping(ChallengeDocument::getTimesBookmark, ChallengeDto::setTimesBookmark)
                    .addMapping(ChallengeDocument::getTimesSolved, ChallengeDto::setTimesSolved);
            mapper.addConverter(converterFromLocalDateTimeToString);
        }

        if(dtoClass.isAssignableFrom(LanguageDto.class)) {
            mapper.createTypeMap(LanguageDocument.class, LanguageDto.class)
                    .addMapping(LanguageDocument::getIdLanguage,LanguageDto::setLanguageId);
        }

        if(dtoClass.isAssignableFrom(TagDto.class)) {
            mapper.createTypeMap(TagDocument.class, TagDto.class)
                    .addMapping(TagDocument::getIdTag,TagDto::setTagId)
                    .addMapping(TagDocument::getTagName, TagDto::setTagName)
                    .addMapping(TagDocument::getTagDescription, TagDto::setTagDescription)
                    .addMapping(TagDocument::getLanguageId, TagDto::setLanguageId);
        }

        if (dtoClass.isAssignableFrom(ResourceDto.class) && document instanceof ResourceDocument) {
            mapper.createTypeMap(ResourceDocument.class, ResourceDto.class)
                    .addMapping(ResourceDocument::getResourceId, ResourceDto::setResourceId)
                    .addMapping(ResourceDocument::getTitle, ResourceDto::setTitle)
                    .addMapping(ResourceDocument::getDescription, ResourceDto::setDescription)
                    .addMapping(ResourceDocument::getUrl, ResourceDto::setUrl)
                    .addMapping(ResourceDocument::getTopic, ResourceDto::setTopic)
                    .addMapping(ResourceDocument::getContentType, ResourceDto::setContentType)
                    .addMapping(ResourceDocument::getChallengeIds, ResourceDto::setChallengeIds);
        }

        return mapper.map(document, dtoClass);
    }



}

// Node: remove
package com.itachallenge.challenge.config.dbchangelog;

import com.itachallenge.challenge.document.LanguageDocument;
import com.mongodb.reactivestreams.client.MongoDatabase;
import io.mongock.api.annotations.*;
import io.mongock.driver.mongodb.reactive.util.MongoSubscriberSync;
import io.mongock.driver.mongodb.reactive.util.SubscriberSync;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.mongodb.core.ReactiveMongoTemplate;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.stereotype.Component;

import java.util.UUID;

import static org.springframework.data.mongodb.core.query.Criteria.where;

@Component
@ChangeUnit(id = "DatabaseInitalizerDemo", order = "1", author = "Ernesto Arcos / Pedro López")
public class DatabaseInitializer {

    Query query = new Query(where("_id").ne(null));
    private final Logger logger = LoggerFactory.getLogger(DatabaseInitializer.class);
    private static final String COLLECTION_NAME = "mongockDemo";

    // Method to create a new collection before the execution of the change unit
    @BeforeExecution
    public void createCollection(MongoDatabase mongoDatabase) {
        SubscriberSync<Void> subscriber = new MongoSubscriberSync<>();

        mongoDatabase.createCollection(COLLECTION_NAME).subscribe(subscriber);
        subscriber.await();

        logger.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~");
        logger.info("mongockDemo collection created");
    }

    // Method to rollback the changes before the execution of the change unit, in case of any failure
    @RollbackBeforeExecution
    public void rollbackBeforeExecution(MongoDatabase mongoDatabase) {
        SubscriberSync<Void> subscriber = new MongoSubscriberSync<>();

        mongoDatabase.getCollection(COLLECTION_NAME).drop().subscribe(subscriber);
        subscriber.await();

        logger.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~");
        logger.info("mongockDemo collection droped");
    }

    // Method to execute the changes in the database
    @Execution
    public void execution(ReactiveMongoTemplate reactiveMongoTemplate) {
        LanguageDocument languageDocument = new LanguageDocument(UUID.randomUUID(), "JAVA", null);
        reactiveMongoTemplate.save(languageDocument, COLLECTION_NAME)
                .doOnSuccess(success -> logger.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\nexecution"))
                .subscribe();
    }

    // Method to rollback the changes in case of any failure during the execution
    @RollbackExecution
    public void rollback(ReactiveMongoTemplate reactiveMongoTemplate) {
        reactiveMongoTemplate.remove(query, COLLECTION_NAME)
                .doOnSuccess(success -> logger.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\nrollback"))
                .then();
    }
}


// Node: rollback
package com.itachallenge.challenge.config.dbchangelog;

import com.mongodb.client.result.UpdateResult;
import com.mongodb.reactivestreams.client.MongoClient;
import com.mongodb.reactivestreams.client.MongoCollection;
import io.mongock.api.annotations.ChangeUnit;
import io.mongock.api.annotations.Execution;
import io.mongock.api.annotations.RollbackExecution;
import org.bson.Document;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.mongodb.core.ReactiveMongoTemplate;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.data.mongodb.core.query.Update;
import reactor.core.publisher.Mono;

import static org.springframework.data.mongodb.core.query.Criteria.where;
import static org.springframework.data.mongodb.core.query.Query.query;
import static org.springframework.data.mongodb.core.query.Update.update;


/*
 * This class is a change log that updates the database by adding a new field to all documents in a collection,
 * then updates the field name in all documents in the collection, and modifies text in the field.
 * The class uses the reactive MongoDB driver to interact with the database.
 * The class is annotated with @ChangeUnit, which specifies the id, order, and author of the change log.
 * The class do an intentional rollback of the changes made in the execution method to demonstrate the rollback feature.
 * If you want to do a new Order, you can do a new class with the same structure and change the order in the annotation.
 *
 * Author: Dani Diaz
 */

@ChangeUnit(id="DatabaseUpdaterDemo", order = "2", author = "Daniel Diaz")
public class DatabaseUpdater {
    private static final Logger logger = LoggerFactory.getLogger(DatabaseUpdater.class);
    private final ReactiveMongoTemplate reactiveMongoTemplate;

    private static final String DATABASE_NAME = "challenges";
    private static final String COLLECTION_NAME = "mongockDemo";
    private static final String FIELD_NAME = "language_name";
    private static final String NEW_FIELD_NAME = "Language Name Updated";
    private static final String STATE_FIELD = "State";
    private static final String ERROR_UPDATE = "Error during update: {}";
    private static final String EXIST = "$exists";
    // Constructor to initialize the ReactiveMongoTemplate
    public DatabaseUpdater(ReactiveMongoTemplate reactiveMongoTemplate) {
        this.reactiveMongoTemplate = reactiveMongoTemplate;
    }

    // Execution method that is called to perform the database update operations
    @Execution
    public void execution(MongoClient client) {
        logger.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\nUpdater execution started");

        addFieldToAllDocuments(reactiveMongoTemplate);
        logger.info("Field added to all documents");

        updateFieldInCollection(client);
        logger.info("Field updated in collection");
        logger.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\nUpdater execution completed successfully");
    }

    // Rollback method that is called to revert the database update operations in case of any failure
    @RollbackExecution
    public void rollBackExecution(MongoClient client) {
        logger.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\nRollback execution started");
        rollbackUpdateFieldInCollection(client);
        logger.info("Field updated in collection rolled back");

        removeFieldToAllDocuments(reactiveMongoTemplate);
        logger.info("Field removed from all documents");
        logger.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\nRollback execution completed successfully");

    }

    // Method to update a field in a collection
    public void updateFieldInCollection(MongoClient client){
        MongoCollection<Document> collection = client.getDatabase(DATABASE_NAME).getCollection(COLLECTION_NAME);
        Mono.from(collection.updateMany(
                        new Document(FIELD_NAME, new Document(EXIST, true)),
                        new Document("$rename", new Document(FIELD_NAME, NEW_FIELD_NAME))
                )).doOnSuccess(updateResult ->
                        logger.info("Field '{}' renamed to '{}'", FIELD_NAME, NEW_FIELD_NAME))
                .doOnError(error ->
                        logger.error(ERROR_UPDATE, error.getMessage()))
                .subscribe();
    }
    // Method to roll back the update operation performed on a field in a collection
    public void rollbackUpdateFieldInCollection(MongoClient client){
        MongoCollection<Document> collection = client.getDatabase(DATABASE_NAME).getCollection(COLLECTION_NAME);
        Mono.from(collection.updateMany(
                        new Document(NEW_FIELD_NAME, new Document(EXIST, true)),
                        new Document("$rename", new Document(NEW_FIELD_NAME, FIELD_NAME))
                )).doOnSuccess(updateResult ->
                        logger.info("Field '{}' renamed back to '{}'", NEW_FIELD_NAME, FIELD_NAME))
                .doOnError(error ->
                        logger.error("Error during rollback: {}", error.getMessage()))
                .subscribe();
    }


    // Method to add a new field to all documents in a collection
    public void addFieldToAllDocuments(ReactiveMongoTemplate reactiveMongoTemplate) {
        reactiveMongoTemplate.updateMulti(
                query(where(FIELD_NAME).exists(true)), // Query to match all documents with the FIELD_NAME
                update(STATE_FIELD, "ACTIVE"),
                COLLECTION_NAME
        ).doOnSuccess(result -> {
            logger.info("Matched count: {}", result.getMatchedCount());
            logger.info("Modified count: {}", result.getModifiedCount());
        }).doOnError(error -> logger.error(ERROR_UPDATE, error.getMessage())).subscribe();
    }

    // Method to remove a field from all documents in a collection
    public void removeFieldToAllDocuments(ReactiveMongoTemplate reactiveMongoTemplate) {
        Query query = Query.query(where(FIELD_NAME).exists(true));
        reactiveMongoTemplate.updateMulti(query, new Update().unset(STATE_FIELD), COLLECTION_NAME)
                .defaultIfEmpty(UpdateResult.unacknowledged())
                .doOnSuccess(result -> {
                    logger.info("Matched count: {}", result.getMatchedCount());
                    logger.info("Modified count: {}", result.getModifiedCount());
                })
                .doOnError(error -> logger.error(ERROR_UPDATE, error.getMessage()))
                .subscribe();
    }
}


// Node: getDatabase
// Node: updateMany
package com.itachallenge.challenge.config.dbchangelog;

import com.mongodb.reactivestreams.client.MongoClient;
import com.mongodb.reactivestreams.client.MongoCollection;
import io.mongock.api.annotations.ChangeUnit;
import io.mongock.api.annotations.Execution;
import io.mongock.api.annotations.RollbackExecution;
import org.bson.Document;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import reactor.core.publisher.Mono;

import static com.mongodb.client.model.Updates.rename;

/*
 * This class is a change log that updates the database by adding a new field to all documents in a collection,
 * then updates the field name in all documents in the collection.
 * The class uses the reactive MongoDB driver to interact with the database.
 * The class is annotated with @ChangeUnit, which specifies the id, order, and author of the change log.
 * The class do an intentional rollback of the changes made in the execution method to demonstrate the rollback feature.
 * If you want to do a new Order, you can do a new class with the same structure and change the order in the annotation.
 *
 * @Author: Dani Diaz
 */

@Component
@ChangeUnit(id = "Intentional Rollback order", order = "5", author = "Daniel Diaz")
public class DataBaseRollback {

    private static final Logger logger = LoggerFactory.getLogger(DataBaseRollback.class);

    private static final String DATABASE_NAME = "challenges";
    private static final String COLLECTION_NAME = "mongockDemo";
    private static final String FIELD_NAME_UPDATED = "Language Rollbacked";
    private static final String FIELD_NAME = "Language Name Updated";


    @Execution
    public void execution(MongoClient client) {
        logger.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\nUpdater execution started");

            updateFieldInCollection(client);
            logger.info("Field updated in collection");
    }

    @RollbackExecution
    public void rollBackExecution(MongoClient client) {
        logger.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\nRollback execution started");

        rollbackUpdateFieldInCollection(client);
        updateTextInField(client);
        logger.info("Field updated in collection rolled back");
        logger.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\nRollback execution completed successfully");

    }

    public void updateFieldInCollection(MongoClient client) {

        MongoCollection<Document> collection = client.getDatabase(DATABASE_NAME).getCollection(COLLECTION_NAME);
        Document updateQuery = new Document("invalidOperator", new Document("$invalid", "someValue"));

        Mono.from(collection.updateMany(
                        new Document(FIELD_NAME_UPDATED, new Document("$exists", true)),
                        updateQuery))
                .doOnSuccess(updateResult -> logger.info("Field '{}' renamed to '{}'", FIELD_NAME, FIELD_NAME_UPDATED))
                .doOnError(error -> logger.error("Update failed: {}", error.getMessage()))
                .block();
    }


    public void updateTextInField(MongoClient client) {
        MongoCollection<Document> collection = client.getDatabase(DATABASE_NAME).getCollection(COLLECTION_NAME);

        Document filter = new Document(FIELD_NAME_UPDATED, "LanguageDemo");
        Document update = new Document("$set", new Document(FIELD_NAME_UPDATED, "LanguageUpdated"));

        Mono.from(collection.updateMany(filter, update))
                .doOnSuccess(updateResult -> logger.info("Field '{}' updated from 'LanguageDemo' to 'LanguageUpdateD'", FIELD_NAME_UPDATED))
                .block();
    }



    public void rollbackUpdateFieldInCollection(MongoClient client) {

        MongoCollection<Document> collection = client.getDatabase(DATABASE_NAME).getCollection(COLLECTION_NAME);
        Mono.from(collection.updateMany(
                        new Document(FIELD_NAME, new Document("$exists", true)),
                        rename(FIELD_NAME, FIELD_NAME_UPDATED)))
                .doOnSuccess(updateResult -> logger.info("Field '{}' renamed back to '{}'", FIELD_NAME, FIELD_NAME_UPDATED))
                .block();
    }
}


// Node: rename
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


// Node: shouldInstantiateDocumentWithNoArgsConstructor
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


// Node: provideInvalidEnumValues
// Node: isFavorite
// Node: getTimesFavorited
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


// Node: createNewResource_ValidRequest_ReturnsCreatedResource
// Node: createNewResource_MissingRequiredFields_ReturnsBadRequest
// Node: getResourcesByChallengeId_ValidId_ReturnsResources
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


// Node: saveResourceTest
// Node: saveMultipleResourcesTest
// Node: countResourcesAfterSaveAndDeleteTest
// Node: findByChallengeIdsContaining_WhenChallengeIdExists_ReturnsResources
package com.itachallenge.challenge.document;

import com.itachallenge.challenge.enums.AssociationType;
import com.itachallenge.challenge.enums.ResourceContentType;
import com.itachallenge.challenge.enums.Topic;
import org.junit.jupiter.api.Test;

import java.util.Collections;
import java.util.List;
import java.util.UUID;

import static org.hibernate.validator.internal.util.Contracts.assertTrue;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertNull;
import static org.junit.jupiter.api.Assertions.assertEquals;

public class ResourceTest {

    // utilitzo el builder per no haver de posar tots els valors nulls
    @Test
    void getUuid() {
        UUID uuid = UUID.randomUUID();
        ResourceDocument resource = ResourceDocument.builder()
                .resourceId(uuid)
                .build();
        assertEquals(uuid, resource.getResourceId());
    }

    @Test
    void getTitle() {
        String title = "Sample Title";
        ResourceDocument resource = ResourceDocument.builder()
                .title(title)
                .build();
        assertEquals(title, resource.getTitle());
    }

    @Test
    void getDescription() {
        String description = "Sample Description";
        ResourceDocument resource = ResourceDocument.builder()
                .description(description)
                .build();
        assertEquals(description, resource.getDescription());
    }

    @Test
    void getUrl() {
        String url = "https://example.com";
        ResourceDocument resource = ResourceDocument.builder()
                .url(url)
                .build();
        assertEquals(url, resource.getUrl());
    }

    @Test
    void getTopic() {
        Topic topic = Topic.DEBUGGING;
        ResourceDocument resource = ResourceDocument.builder()
                .topic(topic)
                .build();
        assertEquals(topic, resource.getTopic());
    }

    @Test
    void getContentType() {
        ResourceContentType contentType = ResourceContentType.BLOG;
        ResourceDocument resource = ResourceDocument.builder()
                .contentType(contentType)
                .build();
        assertEquals(contentType, resource.getContentType());
    }

    @Test
    void getChallengeIds() {
        List<UUID> challengeIds = List.of(UUID.randomUUID(), UUID.randomUUID());
        ResourceDocument resource = ResourceDocument.builder()
                .challengeIds(challengeIds)
                .build();
        assertEquals(challengeIds, resource.getChallengeIds());
    }

    @Test
    void testEmptyResourceDocument() {
        ResourceDocument resource = ResourceDocument.builder().build();

        assertNull(resource.getResourceId());
        assertNull(resource.getTitle());
        assertNull(resource.getDescription());
        assertNull(resource.getUrl());
        assertNull(resource.getTopic());
        assertNull(resource.getContentType());
        assertNull(resource.getChallengeIds());
        assertNull(resource.getAssociationType());
    }

    @Test
    void testEmptyChallengeIds() {
        ResourceDocument resource = ResourceDocument.builder()
                .challengeIds(List.of())
                .build();
        assertTrue(resource.getChallengeIds().isEmpty(), "ChallengeIds should be empty.");
    }

    @Test
    void testNullFields() {
        ResourceDocument resource = ResourceDocument.builder()
                .resourceId(null)
                .title(null)
                .description(null)
                .url(null)
                .topic(null)
                .contentType(null)
                .challengeIds(null)
                .associationType(null)
                .build();

        assertNull(resource.getResourceId());
        assertNull(resource.getTitle());
        assertNull(resource.getDescription());
        assertNull(resource.getUrl());
        assertNull(resource.getTopic());
        assertNull(resource.getContentType());
        assertNull(resource.getChallengeIds());
        assertNull(resource.getAssociationType());
    }

    @Test
    void testResourceDocumentWithNonNullValues() {
        UUID resourceId = UUID.randomUUID();
        String title = "Test Title";
        String description = "Test Description";
        String url = "https://test.com";
        Topic topic = Topic.DEBUGGING;
        ResourceContentType contentType = ResourceContentType.VIDEO;
        List<UUID> challengeIds = List.of(UUID.randomUUID());
        AssociationType associationType = AssociationType.ALLSAMETOPIC;

        ResourceDocument resource = ResourceDocument.builder()
                .resourceId(resourceId)
                .title(title)
                .description(description)
                .url(url)
                .topic(topic)
                .contentType(contentType)
                .challengeIds(challengeIds)
                .associationType(associationType)
                .build();

        assertEquals(resourceId, resource.getResourceId());
        assertEquals(title, resource.getTitle());
        assertEquals(description, resource.getDescription());
        assertEquals(url, resource.getUrl());
        assertEquals(topic, resource.getTopic());
        assertEquals(contentType, resource.getContentType());
        assertEquals(challengeIds, resource.getChallengeIds());
        assertEquals(associationType, resource.getAssociationType());
    }

    @Test
    void testModifyResourceDocument() {
        ResourceDocument resource = ResourceDocument.builder()
                .resourceId(UUID.randomUUID())
                .title("Initial Title")
                .description("Initial Description")
                .url("https://initial.com")
                .build();

        resource.setTitle("Updated Title");
        resource.setDescription("Updated Description");

        assertEquals("Updated Title", resource.getTitle());
        assertEquals("Updated Description", resource.getDescription());
    }

    @Test
    void testResourceDocumentWithEmptyLists() {
        ResourceDocument resource = ResourceDocument.builder()
                .resourceId(UUID.randomUUID())
                .title("Title")
                .description("Description")
                .url("https://example.com")
                .topic(Topic.DEBUGGING)
                .contentType(ResourceContentType.VIDEO)
                .challengeIds(Collections.emptyList())
                .associationType(AssociationType.NONE)
                .build();

        assertNotNull(resource);
        assertTrue(resource.getChallengeIds().isEmpty(), "ChallengeIds should be empty.");
    }

    @Test
    void testDefaultValues() {
        ResourceDocument resource = new ResourceDocument();
        assertNull(resource.getResourceId());
        assertNull(resource.getTitle());
        assertNull(resource.getDescription());
        assertNull(resource.getUrl());
        assertNull(resource.getTopic());
        assertNull(resource.getContentType());
        assertNull(resource.getChallengeIds());
        assertNull(resource.getAssociationType());
    }

    @Test
    void testResourceDocumentWithNullTopic() {
        ResourceDocument resource = ResourceDocument.builder()
                .resourceId(UUID.randomUUID())
                .title("Title")
                .description("Description")
                .url("https://example.com")
                .topic(null)
                .contentType(ResourceContentType.BLOG)
                .build();

        assertNull(resource.getTopic());
    }




}



// Node: testEmptyResourceDocument
// Node: testEmptyChallengeIds
// Node: testNullFields
// Node: testResourceDocumentWithNonNullValues
// Node: testModifyResourceDocument
// Node: testResourceDocumentWithEmptyLists
// Node: ResourceDocument
// Node: testResourceDocumentWithNullTopic
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

// Node: increaseTimesSolved_whenTimesSolvedIsNull_shouldSetToOne
// Node: increaseTimesSolved_whenTimesSolvedIsNonNull_shouldIncrementByOne
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

// Node: addChallenge_test_success
// Node: addChallenge_test_emptyTags
// Node: setTimesFavorite
// Node: updateChallenge_success_test
// Node: consumeNextWith
// Node: assertAll
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


// Node: addChallengeToFavorites_WhenAdded_IncreasesTimesFavoriteAndReturnsFavoriteDTO
// Node: addChallengeToFavorites_WhenAddedAndInitialTimesFavoriteIsNull_IncreasesTimesFavoriteAndReturnsFavoriteDTO
// Node: addChallengeToFavorites_WhenNotAdded_NotIncreaseTimesFavoriteAndReturnsFavoriteDTO
// Node: addChallengeToFavorites_WhenNotAddedAndTimesFavoriteIsNullOrZero_SetTimesFavoriteToOneAndReturnsFavoriteDTO
// Node: removeChallengeFromFavorites_WhenRemoved_DecreasesTimesFavoriteAndReturnsFavoriteDTO
// Node: removeChallengeFromFavorites_WhenRemovedAndInitialTimesFavoriteIsNull_SetsTimesFavoriteToZeroAndReturnsFavoriteDTO
// Node: removeChallengeFromFavorites_WhenRemovedAndInitialTimesFavoriteIsZero_SetsTimesFavoriteToZeroAndReturnsFavoriteDTO
// Node: removeChallengeFromFavorites_WhenNotRemoved_NotChangeTimesFavoriteAndReturnsFavoriteDTO
// Node: removeChallengeFromFavorites_WhenNotRemovedAndTimesFavoriteIsNullOrZero_SetTimesFavoriteToZeroAndReturnsFavoriteDTO
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


// Node: createResource_WithValidData_ResourceCreated
// Node: createResource_WithMissingContentType_ShouldThrowError
// Node: createResource_WithnullTopicType_ShouldThrowError
// Node: createResource_WithAssociationTypeChoose_ShouldReturnUpdatedResource
// Node: atMost
// Node: createResource_WithAssociationTypeChoose_NoChallengesFound_ShouldThrowError
// Node: createResource_WithAssociationTypeNone_ShouldSaveResource
// Node: createResource_WithChooseAssociationType_NoChallenges_ShouldNotSave
// Node: createResource_WithAssociationTypeALLSAMETOPIC_ShouldPopulateChallengeIds
// Node: createResource_WithChooseAssociationType_NoChallengesFound_ShouldThrowError
// Node: createResource_WithAssociationTypeALLSAMETOPIC_MultipleChallenges_ShouldPopulateChallengeIds
// Node: createResource_WithFailedConversion_ShouldThrowError
package com.itachallenge.challenge.helper;

import com.itachallenge.challenge.document.ResourceDocument;
import com.itachallenge.challenge.dto.ResourceDto;
import com.itachallenge.challenge.enums.ResourceContentType;
import com.itachallenge.challenge.enums.Topic;
import org.junit.jupiter.api.Test;
import reactor.core.publisher.Flux;

import java.util.List;
import java.util.UUID;

import static org.junit.Assert.*;

public class ResourceDocumentToDtoConverterTest {
    private final DocumentToDtoConverter<ResourceDocument, ResourceDto> converter = new DocumentToDtoConverter<>();

    @Test
    void convertDtoToDocumentTest() {
        UUID resourceId = UUID.fromString("123e4567-e89b-12d3-a456-426614174000");
        List<UUID> challengeIds = List.of(
                UUID.fromString("f47ac10b-58cc-4372-a567-0e02b2c3d479"),
                UUID.fromString("550e8400-e29b-41d4-a716-446655440000")
        );

        ResourceDto dto = ResourceDto.builder()
                .resourceId(resourceId)
                .title("DEBUGGING FOR THE FIRST TIME")
                .description("A guide on how to start debugging")
                .url("https://youtubetutorial.com/debugging")
                .topic(Topic.COMPONENTS)
                .contentType(ResourceContentType.BLOG)
                .challengeIds(challengeIds)
                .build();

        ResourceDocument document = converter.convertDtoToDocument(dto, ResourceDocument.class);

        assertNotNull(document);
        assertEquals(dto.getResourceId(), document.getResourceId());
        assertEquals(dto.getTitle(), document.getTitle());
        assertEquals(dto.getDescription(), document.getDescription());
        assertEquals(dto.getUrl(), document.getUrl());
        assertEquals(dto.getTopic(), document.getTopic());
        assertEquals(dto.getContentType(), document.getContentType());
        assertEquals(dto.getChallengeIds(), document.getChallengeIds());
    }

    @Test
    void convertDocumentToDtoTest() {
        UUID resourceId = UUID.fromString("123e4567-e89b-12d3-a456-426614174000");
        List<UUID> challengeIds = List.of(
                UUID.fromString("f47ac10b-58cc-4372-a567-0e02b2c3d479"),
                UUID.fromString("550e8400-e29b-41d4-a716-446655440000")
        );

        ResourceDocument document = ResourceDocument.builder()
                .resourceId(resourceId)
                .title("DEBUGGING FOR THE FIRST TIME")
                .description("A guide on how to start debugging")
                .url("https://youtubetutorial.com/debugging")
                .topic(Topic.COMPONENTS)
                .contentType(ResourceContentType.BLOG)
                .challengeIds(challengeIds)
                .build();

        ResourceDto dto = converter.convertDocumentToDto(document, ResourceDto.class);

        assertNotNull(dto);
        assertEquals(document.getResourceId(), dto.getResourceId());
        assertEquals(document.getTitle(), dto.getTitle());
        assertEquals(document.getDescription(), dto.getDescription());
        assertEquals(document.getUrl(), dto.getUrl());
        assertEquals(document.getTopic(), dto.getTopic());
        assertEquals(document.getContentType(), dto.getContentType());
        assertEquals(document.getChallengeIds(), dto.getChallengeIds());
    }

    @Test
    void convertDocumentFluxToDtoFluxTest() {
        UUID resourceId = UUID.fromString("123e4567-e89b-12d3-a456-426614174000");
        List<UUID> challengeIds = List.of(
                UUID.fromString("f47ac10b-58cc-4372-a567-0e02b2c3d479"),
                UUID.fromString("550e8400-e29b-41d4-a716-446655440000")
        );

        ResourceDocument document1 = ResourceDocument.builder()
                .resourceId(resourceId)
                .title("DEBUGGING FOR THE FIRST TIME")
                .description("A guide on how to start debugging")
                .url("https://youtubetutorial.com/debugging")
                .topic(Topic.COMPONENTS)
                .contentType(ResourceContentType.BLOG)
                .challengeIds(challengeIds)
                .build();

        ResourceDocument document2 = ResourceDocument.builder()
                .resourceId(UUID.randomUUID())
                .title("ANOTHER TITLE")
                .description("A different guide")
                .url("https://anotherurl.com")
                .topic(Topic.DEBUGGING)
                .contentType(ResourceContentType.BLOG)
                .challengeIds(challengeIds)
                .build();

        Flux<ResourceDocument> documentFlux = Flux.just(document1, document2);
        Flux<ResourceDto> dtoFlux = converter.convertDocumentFluxToDtoFlux(documentFlux, ResourceDto.class);

        assertNotNull(dtoFlux);
        assertEquals(2, dtoFlux.collectList().block().size());
    }

    @Test
    void convertDtoToDocument_WhenNullValues_ReturnsCorrectDocument() {

        ResourceDto dto = ResourceDto.builder()
                .resourceId(UUID.fromString("123e4567-e89b-12d3-a456-426614174000"))
                .title(null)
                .description(null)
                .url(null)
                .topic(null)
                .contentType(null)
                .challengeIds(null)
                .build();


        ResourceDocument document = converter.convertDtoToDocument(dto, ResourceDocument.class);


        assertNotNull(document);
        assertEquals(dto.getResourceId(), document.getResourceId());
        assertNull(document.getTitle());
        assertNull(document.getDescription());
        assertNull(document.getUrl());
        assertNull(document.getTopic());
        assertNull(document.getContentType());
        assertNull(document.getChallengeIds());
    }

    @Test
    void convertDocumentToDto_WhenNullValues_ReturnsCorrectDto() {
        ResourceDocument document = ResourceDocument.builder()
                .resourceId(UUID.fromString("123e4567-e89b-12d3-a456-426614174000"))
                .title(null)
                .description(null)
                .url(null)
                .topic(null)
                .contentType(null)
                .challengeIds(null)
                .build();

        ResourceDto dto = converter.convertDocumentToDto(document, ResourceDto.class);

        assertNotNull(dto);
        assertEquals(document.getResourceId(), dto.getResourceId());
        assertNull(dto.getTitle());
        assertNull(dto.getDescription());
        assertNull(dto.getUrl());
        assertNull(dto.getTopic());
        assertNull(dto.getContentType());
        assertNull(dto.getChallengeIds());
    }

    @Test
    void convertDocumentFluxToDtoFlux_WhenMultipleDocuments_ReturnsCorrectDtoFlux() {
        ResourceDocument document1 = ResourceDocument.builder()
                .resourceId(UUID.fromString("123e4567-e89b-12d3-a456-426614174000"))
                .title("Debugging 101")
                .description("An introductory guide to debugging")
                .url("https://example.com/debugging101")
                .topic(Topic.DEBUGGING)
                .contentType(ResourceContentType.BLOG)
                .challengeIds(List.of(UUID.randomUUID()))
                .build();

        ResourceDocument document2 = ResourceDocument.builder()
                .resourceId(UUID.fromString("789e4567-e89b-12d3-a456-426614174111"))
                .title("Advanced Debugging")
                .description("A deep dive into debugging")
                .url("https://example.com/advanceddebugging")
                .topic(Topic.DEBUGGING)
                .contentType(ResourceContentType.BLOG)
                .challengeIds(List.of(UUID.randomUUID(), UUID.randomUUID()))
                .build();

        Flux<ResourceDocument> documentFlux = Flux.just(document1, document2);


        Flux<ResourceDto> dtoFlux = converter.convertDocumentFluxToDtoFlux(documentFlux, ResourceDto.class);

        List<ResourceDto> dtoList = dtoFlux.collectList().block();
        assertNotNull(dtoList);
        assertEquals(2, dtoList.size());
        assertEquals(document1.getResourceId(), dtoList.get(0).getResourceId());
        assertEquals(document2.getResourceId(), dtoList.get(1).getResourceId());
    }
    @Test
    void convertDocumentToDto_WhenChallengeIdsEmpty_ReturnsCorrectDto() {

        ResourceDocument document = ResourceDocument.builder()
                .resourceId(UUID.fromString("123e4567-e89b-12d3-a456-426614174000"))
                .title("Debugging Guide")
                .description("A complete guide to debugging")
                .url("https://debuggingguide.com")
                .topic(Topic.DEBUGGING)
                .contentType(ResourceContentType.BLOG)
                .challengeIds(List.of())
                .build();

        ResourceDto dto = converter.convertDocumentToDto(document, ResourceDto.class);

        assertNotNull(dto);
        assertEquals(document.getResourceId(), dto.getResourceId());
        assertEquals(document.getTitle(), dto.getTitle());
        assertEquals(document.getDescription(), dto.getDescription());
        assertEquals(document.getUrl(), dto.getUrl());
        assertEquals(document.getTopic(), dto.getTopic());
        assertEquals(document.getContentType(), dto.getContentType());
        assertTrue(dto.getChallengeIds().isEmpty());
    }

    @Test
    void convertDtoToDocument_WhenChallengeIdsEmpty_ReturnsCorrectDocument() {
        ResourceDto dto = ResourceDto.builder()
                .resourceId(UUID.fromString("123e4567-e89b-12d3-a456-426614174000"))
                .title("Debugging Guide")
                .description("A complete guide to debugging")
                .url("https://debuggingguide.com")
                .topic(Topic.DEBUGGING)
                .contentType(ResourceContentType.BLOG)
                .challengeIds(List.of())
                .build();

        ResourceDocument document = converter.convertDtoToDocument(dto, ResourceDocument.class);

        assertNotNull(document);
        assertEquals(dto.getResourceId(), document.getResourceId());
        assertEquals(dto.getTitle(), document.getTitle());
        assertEquals(dto.getDescription(), document.getDescription());
        assertEquals(dto.getUrl(), document.getUrl());
        assertEquals(dto.getTopic(), document.getTopic());
        assertEquals(dto.getContentType(), document.getContentType());
        assertTrue(document.getChallengeIds().isEmpty());
    }

}



// Node: convertDtoToDocumentTest
// Node: convertDocumentToDtoTest
// Node: convertDocumentFluxToDtoFluxTest
// Node: convertDtoToDocument_WhenNullValues_ReturnsCorrectDocument
// Node: convertDocumentToDto_WhenNullValues_ReturnsCorrectDto
// Node: convertDocumentFluxToDtoFlux_WhenMultipleDocuments_ReturnsCorrectDtoFlux
// Node: convertDocumentToDto_WhenChallengeIdsEmpty_ReturnsCorrectDto
// Node: convertDtoToDocument_WhenChallengeIdsEmpty_ReturnsCorrectDocument
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



// Node: builderAndGettersSettersTest
// Node: equalsAndHashCodeTest
// Node: testInvalidResourceDto
// Node: testToBuilder
// Node: toBuilder
// Node: testSerializationWithNullFields
// Node: shouldFailWhenFieldsMissingOrEmpty
// Node: shouldFailWhenTopicNull
// Node: shouldFailWhenContentTypeNull
// Node: shouldFailWhenChallengeIdsNull
// Node: shouldPassWhenValid
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








// Node: testDeserializationWithMissingTopic
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


// Node: shouldFailWhenStringFieldsEmpty
// Node: challengeTitle
// Node: language
// Node: solution
// Node: shouldFailWhenTopicIsNull
// Node: shouldFailWhenTagsListEmpty
package com.itachallenge.challenge.config.dbchangelog;

import com.itachallenge.challenge.document.LanguageDocument;
import com.mongodb.reactivestreams.client.MongoDatabase;
import io.mongock.api.annotations.*;
import io.mongock.driver.mongodb.reactive.util.MongoSubscriberSync;
import io.mongock.driver.mongodb.reactive.util.SubscriberSync;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.mongodb.core.ReactiveMongoTemplate;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.stereotype.Component;

import java.util.UUID;

import static org.springframework.data.mongodb.core.query.Criteria.where;

@Component
@ChangeUnit(id = "DatabaseInitalizerTest", order = "1", author = "Ernesto Arcos / Pedro López")
public class TestDatabaseInitializer {
    Query query = new Query(where("_id").ne(null));
    private final Logger logger = LoggerFactory.getLogger(DatabaseInitializer.class);
    private static final String COLLECTION_NAME = "MongockTest";

    @BeforeExecution
    public void createCollection(MongoDatabase mongoDatabase) {
        SubscriberSync<Void> subscriber = new MongoSubscriberSync<>();

        mongoDatabase.createCollection(COLLECTION_NAME).subscribe(subscriber);
        subscriber.await();

        logger.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~");
        logger.info("mongockTest collection created");
    }

    @RollbackBeforeExecution
    public void rollbackBeforeExecution(MongoDatabase mongoDatabase) {
        SubscriberSync<Void> subscriber = new MongoSubscriberSync<>();

        mongoDatabase.getCollection(COLLECTION_NAME).drop().subscribe(subscriber);
        subscriber.await();

        logger.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~");
        logger.info("mongockTest collection droped");
    }

    @Execution
    public void execution(ReactiveMongoTemplate reactiveMongoTemplate) {
        LanguageDocument languageDocument = new LanguageDocument(UUID.randomUUID(), "LanguageDemo", "https://image-default.com/default.png");
        reactiveMongoTemplate.save(languageDocument, COLLECTION_NAME)
                .doOnSuccess(success -> logger.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\nexecution"))
                .subscribe();
    }

    @RollbackExecution
    public void rollback(ReactiveMongoTemplate reactiveMongoTemplate) {
        reactiveMongoTemplate.remove(query, COLLECTION_NAME)
                .doOnSuccess(success -> logger.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\nrollback"))
                .then();
    }

}


package com.itachallenge.auth.controller;

import com.itachallenge.auth.dto.SwitchRoleRequest;
import com.itachallenge.auth.exception.CustomBadRequestException;
import com.itachallenge.auth.exception.CustomInternalServerErrorException;
import com.itachallenge.auth.service.IAuthService;
import com.itachallenge.auth.service.JwtRoleSwitchService;
import com.itachallenge.auth.service.IAuthJwtFacade;
import com.itachallenge.auth.service.IUserService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import reactor.core.publisher.Mono;

import java.util.HashMap;
import java.util.Map;

@RestController
@Validated
@RequestMapping(value = "/itachallenge/api/v1/auth")
public class AuthController {

    private static final Logger log = LoggerFactory.getLogger(AuthController.class);
    private static final String KEY_IS_VALID = "isValid";
    private static final String KEY_USERNAME = "username";
    public static final String X_GITHUB_USERNAME = "X-Github-Username";
    public static final String X_AUTHENTICATION_STATUS = "X-Authentication-Status";
    private static final String MESSAGE_KEY = "message";
    private static final String LOGOUT_SUCCESS = "Logout successful";

    private final IAuthService authService;

    private final IUserService userService;

    private IAuthJwtFacade authJwtFacade;

    private final String version;

    private final String appName;

    private final JwtRoleSwitchService jwtRoleSwitchService;

    public AuthController(IAuthService authService,
                          IUserService userService,
                          IAuthJwtFacade authJwtFacade,
                          @Value("${spring.application.version}") String version,
                          @Value("${spring.application.name}") String appName, JwtRoleSwitchService jwtRoleSwitchService) {
        this.authService = authService;
        this.userService = userService;
        this.authJwtFacade = authJwtFacade;
        this.version = version;
        this.appName = appName;
        this.jwtRoleSwitchService = jwtRoleSwitchService;
    }

    @GetMapping(value = "/test")
    public String test() {
        return "Hello from ITA ChallengeAuth!!!";
    }


    @PostMapping("/github/authenticate")
    public Mono<ResponseEntity<Map<String, Object>>> authenticateWithGithub(@RequestBody Map<String, String> codeRequest) {
        return authService.exchangeCodeForToken(codeRequest.get("code"))
                .flatMap(authService::validateTokenWithGithub)
                .flatMap(response -> {
                    if (!(boolean) response.get(KEY_IS_VALID)) {
                        return Mono.just(ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                                .header(X_AUTHENTICATION_STATUS, "Failed")
                                .body(response));
                    }
                    String githubUsername = (String) response.get(KEY_USERNAME);
                    return getUserDetailsFromGithubUsername(response, githubUsername);
                })
                .onErrorResume(ex -> {
                    log.error("GitHub authentication error: {}", ex.getMessage());

                    Map<String, Object> errorResponse = new HashMap<>();
                    errorResponse.put(KEY_IS_VALID, false);
                    errorResponse.put(KEY_USERNAME, null);

                    return Mono.just(ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                            .header(X_AUTHENTICATION_STATUS, "Error")
                            .header("X-Error-Message", "An error occurred during authentication.")
                            .body(errorResponse));
                });
    }

    private Mono<ResponseEntity<Map<String, Object>>> getUserDetailsFromGithubUsername(Map<String, Object> response, String githubUsername) {

        return userService.fetchUserData(githubUsername)
                .map(user -> authJwtFacade.generateToken(user.getUsername(), user.getRole(), user.getUuid()))
                .map(token -> {
                    response.put("token", token);
                    return ResponseEntity.ok()
                            .header(X_AUTHENTICATION_STATUS, "Success")
                            .header(X_GITHUB_USERNAME, githubUsername)
                            .body(response);
                })
                .switchIfEmpty(Mono.defer(() -> {
                    response.put(KEY_USERNAME, null);
                    response.put(KEY_IS_VALID, false);
                    response.put(MESSAGE_KEY, "User does not exist in the database");
                    return Mono.just(ResponseEntity.status(HttpStatus.FORBIDDEN)
                            .header("X-Validation-Status", "Forbidden")
                            .header(X_GITHUB_USERNAME, githubUsername)
                            .header("X-Error-Message", "User does not exist in the database")
                            .body(response));
                }))
                .onErrorResume(throwable -> {
                    HttpStatus status = HttpStatus.INTERNAL_SERVER_ERROR;
                    String message = "Unexpected Error Occurred";
                    log.error("Error in the authentication process: {}", throwable.getMessage());

                    if (throwable instanceof CustomBadRequestException) {
                        status = HttpStatus.BAD_REQUEST;
                        message = throwable.getMessage();
                    }else if (throwable instanceof CustomInternalServerErrorException) {
                        message = throwable.getMessage();
                    }
                    response.put(KEY_USERNAME, null);
                    response.put(KEY_IS_VALID, false);
                    response.put(MESSAGE_KEY, message);
                    return Mono.just(ResponseEntity.status(status)
                            .header("X-Validation-Status", "Forbidden")
                            .header(X_GITHUB_USERNAME, githubUsername)
                            .body(response)
                    );
                });
    }


    @GetMapping("/version")
    public Mono<ResponseEntity<Map<String, String>>> getVersion() {
        Map<String, String> response = new HashMap<>();
        response.put("application_name", appName);
        response.put("version", version);
        return Mono.just(ResponseEntity.ok(response));
    }

    @GetMapping("/call-user-test")
    public Mono<String> callUserTest() {
        return userService.callUserTest();
    }

    @PostMapping("/logout")
    public Mono<ResponseEntity<Map<String, String>>> logout(
            @RequestHeader(value = "Authorization", required = false) String authHeader) {
        if (authHeader == null || !authHeader.startsWith("Bearer ")) {
            log.warn("Logout attempt without token or malformed header");
            return Mono.just(ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(Map.of(MESSAGE_KEY, "Authorization header is missing or malformed")));
        }

        String token = authHeader.replace("Bearer ", "").trim();
        authJwtFacade.validateToken(token);
        return Mono.just(ResponseEntity.ok(Map.of(MESSAGE_KEY, "Logout successful")));
    }

    @PostMapping("/switch-role")
    @Operation(
            summary = "Temporarily switch the user's role and return a new token.",
            responses = {
                    @ApiResponse(responseCode = "200", description = "Token generated successfully or expired.",
                            content = @Content(schema = @Schema(implementation = Map.class))),
                    @ApiResponse(responseCode = "400", description = "Invalid role requested."),
                    @ApiResponse(responseCode = "401", description = "Missing or malformed Authorization header or invalid token."),
                    @ApiResponse(responseCode = "500", description = "Unexpected error occurred.")
            }
    )
    public Mono<ResponseEntity<Map<String, String>>> switchRole(
            @RequestHeader(value = "Authorization", required = false) String authHeader,
            @RequestBody SwitchRoleRequest request) {

        String token = authJwtFacade.extractBearerToken(authHeader);
        String newToken = jwtRoleSwitchService.switchRole(token, request.getNewRole());
        log.info("Switch-role successful for token");
        return Mono.just(ResponseEntity.ok(Map.of("token", newToken)));
    }
}

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


package com.itachallenge.auth.config;


import org.springframework.web.reactive.function.client.WebClient;

public class WebClientConfig {
    //@Bean
    public WebClient.Builder webClientBuilder() {
        return WebClient.builder();
    }
}


