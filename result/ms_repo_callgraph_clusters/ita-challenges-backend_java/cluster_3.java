// Cluster 3

// Node: getLogger
// Node: Value
package com.itachallenge.jwtcore.service;

import com.fasterxml.jackson.databind.ObjectMapper;

import io.jsonwebtoken.*;
import io.jsonwebtoken.io.Decoders;
import io.jsonwebtoken.security.Keys;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.crypto.SecretKey;
import java.io.IOException;
import java.util.Date;
import java.util.Map;


@Service
public class JwtService implements IJwtService {

    private static final String BEARER_KEY = "Bearer ";
    private static final Logger log = LoggerFactory.getLogger(JwtService.class);
    private final String jwtSigningKey;
    private final long minutesTillExpiration;

    public JwtService(
            @Value("${token.signing.key}") String jwtSigningKey,
            @Value("${token.expiration.minutes}") Long minutesTillExpiration) {
        this.jwtSigningKey = jwtSigningKey;
        this.minutesTillExpiration = minutesTillExpiration;
    }

    @Override
    public String generateToken(String username, String role, String uuid) {
        JwtBuilder builder = Jwts.builder()
                .subject(username)
                .claim("role", role)
                .claim("uuid", uuid)
                .issuedAt(new Date())
                .expiration(new Date(System.currentTimeMillis() + minutesTillExpiration * 60000))
                .signWith(getSigningKey());
        return builder.compact();
    }

    @Override
    public void validateToken(String token) {
        SecretKey key = getSigningKey();
        try {
            Jwts.parser()
                    .verifyWith(key)
                    .build()
                    .parseSignedClaims(token);
        } catch (ExpiredJwtException e) {
            log.info("Logout with expired token: {}", e.getMessage());
            throw new ExpiredJwtException(e.getHeader(), e.getClaims(), "Token expired but logout successful", e);
        } catch (JwtException e) {
            log.warn("Logout attempt with invalid or tampered token: {}", e.getMessage());
            throw new JwtException("Invalid or tampered token: " + e.getMessage(), e);
        }
    }

    public SecretKey getSigningKey() {
        byte[] keyBytes = Decoders.BASE64.decode(jwtSigningKey);
        return Keys.hmacShaKeyFor(keyBytes);
    }

    @Override
    public Claims extractAllClaims(String token) {
        try {
            return Jwts.parser()
                    .verifyWith(getSigningKey())
                    .build()
                    .parseSignedClaims(token)
                    .getPayload();
        } catch (ExpiredJwtException e) {
            log.info("Token expired at {} for subject {}",
                    e.getClaims().getExpiration(),
                    e.getClaims().getSubject());
            throw new ExpiredJwtException(e.getHeader(), e.getClaims(), "Token expired ", e);
        } catch (JwtException e) {
            log.warn("Invalid or tampered token: {}", e.getMessage());
            throw new JwtException("Invalid or tampered token: " + e.getMessage(), e);
        }
    }

    public String extractBearerToken(String authHeader) {
        if (authHeader == null || !authHeader.startsWith(BEARER_KEY)) {
            throw new JwtException("Authorization header is missing or malformed");
        }
        return authHeader.replace(BEARER_KEY, "").trim();
    }


    @Override
    public String getUserUuIdFromAuthenticationHeader(String authHeader) {
        if (authHeader == null || !authHeader.startsWith("Bearer ")) {
            throw new JwtException("Missing or bad formatted Authorization header");
        }
        String userId = extractUuid(authHeader.replace("Bearer ", ""));
        if (userId == null) {
            throw new JwtException("Invalid Authorization header content");
        }
        return userId;
    }

    private String extractUuid(String token) {
        try {
            return extractAllClaims(token).get("uuid").toString();  // Get "uuid" claim
        } catch (Exception e) {
            log.warn("Invalid token: {}", e.getMessage());
            return null;
        }
    }

}

// Node: startsWith
// Node: replace
// Node: extractUuid
// Node: GetMapping
package com.itachallenge.document.controller;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
@Controller
public class ApiDocsController {

    @GetMapping(value = "/api-docs/all")
    public String getApiDocs() {
        return "redirect:/api-docs";
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-document/src/main/java/com/itachallenge/document/controller/ApiDocsController.java:ApiDocsController.<init>
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


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-document/src/main/java/com/itachallenge/document/controller/DocumentController.java:DocumentController.<init>
// Node: DocumentController
// Node: getVersion
// Node: put
package com.itachallenge.githubcore.service;

import com.itachallenge.githubcore.document.enums.GithubUserStatus;
import com.itachallenge.githubcore.exception.GithubUnavailableException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;


public class GithubApiServiceImpl implements GithubApiService {

    private static final Logger log = LoggerFactory.getLogger(GithubApiServiceImpl.class);
    private final WebClient webClient;

    public GithubApiServiceImpl(WebClient.Builder builder, String baseUrl) {
        this.webClient = builder.baseUrl(baseUrl).build();
    }

    @Override
    public Mono<GithubUserStatus> userExists(String username) {
        return webClient.get()
                .uri("/users/{username}", username)
                .exchangeToMono(response -> {
                    if (response.statusCode().equals(HttpStatus.OK)) {
                        return Mono.just(GithubUserStatus.FOUND);
                    } else if (response.statusCode().equals(HttpStatus.NOT_FOUND)) {
                        log.info("GitHub user not found: {}", username);
                        return Mono.just(GithubUserStatus.NOT_FOUND);
                    } else if (response.statusCode().is5xxServerError()) {
                        log.error("GitHub API error for user: {}", username);
                        return Mono.error(new GithubUnavailableException("GitHub API error"));
                    } else {
                        log.error("Unexpected response from GitHub: {}", response.statusCode());
                        return Mono.error(new GithubUnavailableException("Unexpected response from GitHub"));
                    }
                });

    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/github-core/src/main/java/com/itachallenge/githubcore/service/GithubApiServiceImpl.java:GithubApiServiceImpl.<init>
// Node: GithubApiServiceImpl
// Node: baseUrl
// Node: exchangeToMono
package com.itachallenge.githubcore.config;

import com.itachallenge.githubcore.service.GithubApiServiceImpl;
import com.itachallenge.githubcore.service.GithubApiService;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.client.WebClient;

@Configuration
public class GithubServiceConfig {

    @Value("${github.user-info-uri}")
    private String githubApiUrl;

    @Bean
    public GithubApiService githubApiService(WebClient.Builder webClientBuilder) {
        return new GithubApiServiceImpl(webClientBuilder, githubApiUrl);
    }
}

// Node: repos/cloned_ms_repos/ita-challenges-backend/github-core/src/main/java/com/itachallenge/githubcore/config/GithubServiceConfig.java:GithubServiceConfig.<init>
// Node: githubApiService
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


// Node: repos/cloned_ms_repos/ita-challenges-backend/error-response-core/src/test/java/com/itachallenge/errorcore/dto/APIErrorResponseTest.java:APIErrorResponseTest.<init>
package com.itachallenge.user.controller;

import com.itachallenge.user.dto.AdminCreateUserRequestDto;
import com.itachallenge.user.dto.AdminCreateUserResponseDto;
import com.itachallenge.user.service.IAdminCreateUserService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/itachallenge/api/v1/admin")
public class AdminCreateUserController {

    private final IAdminCreateUserService adminCreateUserService;

    public AdminCreateUserController(IAdminCreateUserService adminCreateUserService) {
        this.adminCreateUserService = adminCreateUserService;
    }

    @PostMapping("/users/create")
    //TODO: it has no validation restriction at the moment, it will be added soon.
    public Mono<ResponseEntity<AdminCreateUserResponseDto>> createUser(
            @Valid @RequestBody AdminCreateUserRequestDto request) {
        return adminCreateUserService.createUser(request)
                .map(userDto -> new ResponseEntity<>(userDto, HttpStatus.CREATED));
    }
}

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/controller/AdminCreateUserController.java:AdminCreateUserController.<init>
// Node: RequestMapping
// Node: AdminCreateUserController
// Node: PostMapping
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


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/controller/UserController.java:UserController.<init>
// Node: UserController
// Node: test
// Node: Operation
// Node: Parameter
// Node: ApiResponse
// Node: Content
// Node: Schema
// Node: ok
// Node: PutMapping
// Node: actions
// Node: DeleteMapping
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

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/controller/userinteraction/bookmark/BookmarkController.java:BookmarkController.<init>
// Node: BookmarkController
package com.itachallenge.user.controller.userinteraction.bookmark;

import com.itachallenge.userinteraction.service.bookmark.BookmarkService;
import io.swagger.v3.oas.annotations.Operation;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;
import java.util.Set;
import java.util.UUID;

@RestController
@RequestMapping("/itachallenge/api/v1/user/users")
public class BookmarkLegacyController {
    private final BookmarkService bookmarkService;

    public BookmarkLegacyController(BookmarkService bookmarkService) {
        this.bookmarkService = bookmarkService;
    }

    /**
     * @deprecated This endpoint is deprecated because the domain logic has moved
     * to a subresource structure. Use {@link BookmarkController#getUserBookmarks(String)} instead.
     */
    @Operation(summary = "DEPRECATED: Use /itachallenge/api/v1/users/{userId}/bookmarks")
    @GetMapping("/{userId}/bookmarks")
    @Deprecated(since = "3.1.4-RELEASE", forRemoval = true)
    public Mono<ResponseEntity<Set<UUID>>> getUserBookmarksLegacy(@PathVariable String userId) {
        return bookmarkService.getUserBookmarks(userId)
                .map(bookmarks -> ResponseEntity.ok()
                        .header("Deprecation", "true")
                        .body(bookmarks));
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/controller/userinteraction/bookmark/BookmarkLegacyController.java:BookmarkLegacyController.<init>
// Node: BookmarkLegacyController
// Node: Deprecated
// Node: getUserBookmarksLegacy
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


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/controller/userinteraction/favorite/FavoriteController.java:FavoriteController.<init>
// Node: FavoriteController
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


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/service/UserSolutionServiceImpl.java:UserSolutionServiceImpl.<init>
// Node: UserSolutionServiceImpl
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

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/service/ChallengeServiceImpl.java:ChallengeServiceImpl.<init>
// Node: ChallengeServiceImpl
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


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/service/AdminCreateUserService.java:AdminCreateUserService.<init>
// Node: AdminCreateUserService
// Node: onErrorMap
package com.itachallenge.user.service;

import com.itachallenge.githubcore.document.enums.GithubUserStatus;
import com.itachallenge.githubcore.exception.GithubUnavailableException;
import com.itachallenge.githubcore.service.GithubApiService;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

@Service
public class ExternalGithubServiceImpl implements ExternalGithubService {

    private final GithubApiService githubApiService;

    public ExternalGithubServiceImpl(GithubApiService githubApiService) {
        this.githubApiService = githubApiService;
    }

    @Override
    public Mono<Boolean> userExists(String username) {
        return githubApiService.userExists(username)
                .map(status -> status != GithubUserStatus.NOT_FOUND)
                .onErrorMap(throwable ->
                    new GithubUnavailableException("Error connecting to GitHub API.", throwable)
                );
    }
}


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


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/service/UserServiceImpl.java:UserServiceImpl.<init>
// Node: UserServiceImpl
package com.itachallenge.user.validator;

import com.itachallenge.user.annotations.GenericUUIDValid;
import jakarta.validation.ConstraintValidator;
import jakarta.validation.ConstraintValidatorContext;
import org.springframework.beans.factory.annotation.Value;

import java.util.regex.Pattern;

public class GenericUUIDValidator implements ConstraintValidator<GenericUUIDValid, String> {
    @Value("${validation.mongodb_pattern}")
    private String uuidPattern;
    Pattern UUID_PATTERN;

    @Override
    public void initialize(GenericUUIDValid constraintAnnotation) {
        this.UUID_PATTERN = Pattern.compile(uuidPattern);
    }

    @Override
    public boolean isValid(String value, ConstraintValidatorContext context) {
        String customMessage = context.getDefaultConstraintMessageTemplate();

        if (value == null) {
            context.disableDefaultConstraintViolation();
            context.buildConstraintViolationWithTemplate(customMessage + ": value is null")
                    .addConstraintViolation();
            return false;
        }

        if (!UUID_PATTERN.matcher(value).matches()) {
            context.disableDefaultConstraintViolation();
            context.buildConstraintViolationWithTemplate(customMessage + ": " + value)
                    .addConstraintViolation();
            return false;
        }

        return true;
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/validator/GenericUUIDValidator.java:GenericUUIDValidator.<init>
// Node: initialize
// Node: compile
package com.itachallenge.user.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.web.embedded.tomcat.TomcatServletWebServerFactory;
import org.springframework.boot.web.servlet.server.ConfigurableServletWebServerFactory;
import org.springframework.boot.web.server.WebServerFactoryCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class ServerConfig {

    @Value("${server.tomcat.max-http-form-post-size}")
    private int maxHttpFormPostSize;

    @Bean
    public WebServerFactoryCustomizer<ConfigurableServletWebServerFactory> webServerFactoryCustomizer() {
        return factory -> {
            if (factory instanceof TomcatServletWebServerFactory) {
                ((TomcatServletWebServerFactory) factory).addConnectorCustomizers(connector -> {
                    connector.setMaxPostSize(maxHttpFormPostSize);
                    connector.setMaxSavePostSize(maxHttpFormPostSize);
                });
            }
        };
    }
}

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/config/ServerConfig.java:ServerConfig.<init>
package com.itachallenge.user.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Configuration
@EnableConfigurationProperties
@ConfigurationProperties
public class PropertiesConfig {
    @Value("${url.max_length}")
    private Integer maxLength;

    public Integer getUrlMaxLength(){return maxLength;}


}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/config/PropertiesConfig.java:PropertiesConfig.<init>
// Node: fromCallable
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


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/proxy/HttpProxy.java:HttpProxy.<init>
// Node: HttpProxy
// Node: clientConnector
// Node: initReactorHttpClient
// Node: getConnectionTimeout
// Node: exchangeStrategies
// Node: initExchangeStrategies
// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/proxy/HttpProxy.java:HttpProxy.initReactorHttpClient
// Node: option
// Node: responseTimeout
// Node: ofMillis
// Node: compress
// Node: doOnConnected
// Node: addHandlerLast
// Node: ReadTimeoutHandler
// Node: WriteTimeoutHandler
// Node: ReactorClientHttpConnector
// Node: codecs
// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/proxy/HttpProxy.java:HttpProxy.getClient
// Node: getClient
package com.itachallenge.challenge.controller;

import com.itachallenge.challenge.dto.FavoriteDto;
import com.itachallenge.common.exception.BadRequestException;
import com.itachallenge.challenge.exception.JwtException;
import com.itachallenge.challenge.service.IFavoriteService;
import com.itachallenge.challenge.service.IChallengeJwtFacade;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;


@RestController
@RequestMapping("/itachallenge/api/v1/favorite/challenges/")
public class FavoriteController {

    private final IFavoriteService favoriteService;
    private final IChallengeJwtFacade challengeJwtFacade;
    private static final Logger log = LoggerFactory.getLogger(FavoriteController.class);

    public FavoriteController(IFavoriteService favoriteService, IChallengeJwtFacade challengeJwtFacade) {
        this.favoriteService = favoriteService;
        this.challengeJwtFacade = challengeJwtFacade;
    }

    @PostMapping("/{challengeId}")
    @Operation(
            operationId = "Add a challenge to User's favorites.",
            summary = "Add a challenge to favorites.",
            description = "The ID Challenge sent through the URI is added to the user's favorites. User Id is determined from the headers.",
            responses = {
                    @ApiResponse(responseCode = "200", content = {@Content(schema = @Schema(implementation = FavoriteDto.class), mediaType = "application/json")}),
                    @ApiResponse(responseCode = "400", description = "Missing or invalid authorization header."),
                    @ApiResponse(responseCode = "404", description = "The Challenge with given Id was not found."),
                    @ApiResponse(responseCode = "500", description = "Internal Server Error")
            }
    )
    public Mono<ResponseEntity<FavoriteDto>> addFavorite(
            @PathVariable String challengeId,
            @RequestHeader(name = "Authorization", required = false) String authHeader) {
        return Mono.fromCallable(() -> challengeJwtFacade.getUserUuIdFromAuthenticationHeader(authHeader))
                .onErrorMap(JwtException.class, e -> new BadRequestException(e.getMessage()))
                .flatMap(userId -> favoriteService.addChallengeToFavorites(challengeId, userId))
                .doOnError(e -> log.error("Failed to add favorite for challengeId {}: {}", challengeId, e.getMessage()))
                .map(ResponseEntity::ok);
    }

    @DeleteMapping("/{challengeId}")
    @Operation(
            operationId = "Remove a challenge from the User's favorites.",
            summary = "Remove a challenge from favorites.",
            description = "The ID Challenge sent through the URI is removed from the user's favorites. User Id is determined from the headers.",
            responses = {
                    @ApiResponse(responseCode = "200", content = {@Content(schema = @Schema(implementation = FavoriteDto.class), mediaType = "application/json")}),
                    @ApiResponse(responseCode = "400", description = "Missing or invalid authorization header."),
                    @ApiResponse(responseCode = "404", description = "The Challenge with given Id was not found."),
                    @ApiResponse(responseCode = "500", description = "Internal Server Error")
            }
    )
    public Mono<ResponseEntity<FavoriteDto>> removeFavorite(
            @PathVariable String challengeId,
            @RequestHeader(name = "Authorization", required = false) String authHeader) {
        return Mono.fromCallable(() -> challengeJwtFacade.getUserUuIdFromAuthenticationHeader(authHeader))
                .onErrorMap(JwtException.class, e -> new BadRequestException(e.getMessage()))
                .flatMap(userId -> favoriteService.removeChallengeFromFavorites(challengeId, userId))
                .map(ResponseEntity::ok);
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/controller/FavoriteController.java:FavoriteController.<init>
// Node: RequestHeader
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


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/controller/LanguageController.java:LanguageController.<init>
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


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/controller/ChallengeSolvedController.java:ChallengeSolvedController.<init>
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


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/controller/TagController.java:TagController.<init>
// Node: parameter
package com.itachallenge.challenge.controller;
import com.itachallenge.challenge.dto.ResourceDto;
import com.itachallenge.challenge.service.IResourceService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import jakarta.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.UUID;

@RestController
@Validated
@RequestMapping(value = "/itachallenge/api/v1/resource")
public class ResourceController {

    private static final Logger log = LoggerFactory.getLogger(ResourceController.class);
    private final IResourceService resourceService;

    public ResourceController(IResourceService resourceService) {
        this.resourceService = resourceService;
    }

    @PostMapping(value = "/new")
    @Operation(
            operationId = "Create a new resource",
            summary = "Creates a new resource and associates it with a challenge based on its topic.",
            description = "If a challenge with the same topic exists, it is automatically assigned. If multiple challenges exist, it can be linked to all or remain unassigned.",
            responses = {
                    @ApiResponse(responseCode = "200", content = {@Content(schema = @Schema(implementation = ResourceDto.class), mediaType = "application/json")}),
                    @ApiResponse(responseCode = "400", description = "Invalid parameters"),
                    @ApiResponse(responseCode = "500", description = "Server error")
            }
    )
    public Mono<ResponseEntity<ResourceDto>> createNewResource(@RequestBody @Valid ResourceDto resourceDto) {
        log.info("Creating a new resource {}", resourceDto);
        return resourceService.createResource(resourceDto)
                .map(createdResource -> ResponseEntity.ok().body(createdResource));
    }


    @GetMapping("/challenge/{challengeId}")
    @Operation(summary = "Get resources by challenge ID")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "Resources found"),
            @ApiResponse(responseCode = "400", description = "Invalid challenge ID"),
            @ApiResponse(responseCode = "404", description = "No resources found"),
            @ApiResponse(responseCode = "500", description = "Internal Server Error")
    })
    public Flux<ResourceDto> getResourcesByChallengeId(@PathVariable UUID challengeId) {
        return resourceService.getResourcesByChallengeId(challengeId);
    }
}



// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/controller/ResourceController.java:ResourceController.<init>
// Node: ResourceController
// Node: createNewResource
// Node: ApiResponses
package com.itachallenge.challenge.controller;

import com.itachallenge.challenge.annotations.ValidGenericPattern;
import com.itachallenge.challenge.config.PropertiesConfig;
import com.itachallenge.challenge.dto.*;
import com.itachallenge.common.exception.BadRequestException;
import com.itachallenge.challenge.exception.JwtException;
import com.itachallenge.challenge.service.IChallengeService;
import com.itachallenge.challenge.service.IChallengeJwtFacade;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.client.discovery.DiscoveryClient;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

@RestController
@Validated
@RequiredArgsConstructor
@RequestMapping(value = "/itachallenge/api/v1/challenge")
public class ChallengeController {

    private static final String DEFAULT_OFFSET = "0";
    private static final String DEFAULT_LIMIT = "200";  //if no limit, all elements (avoid exception with default value 200)
    private static final String LIMIT = "^([1-9]\\d?|1\\d{2}|200)$";  // Integer in range [1, 200]
    private static final String NO_SERVICE = "No Services";
    private static final String INVALID_PARAM = "Invalid parameter";
    private static final String UUID_PATTERN = "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$";
    private static final String STRING_PATTERN = "^[A-Za-z]{1,9}$";  //max 9 characters
    private static final String MESSAGE = "message";

    private static final Logger log = LoggerFactory.getLogger(ChallengeController.class);

    private final PropertiesConfig config;

    private final DiscoveryClient discoveryClient;

    private final IChallengeService challengeService;

    private final IChallengeJwtFacade challengeJwtFacade;

    @Value("${spring.application.version}")
    private String version;

    @Value("${spring.application.name}")
    private String appName;

    @GetMapping(value = "/test")
    public String test() {
        log.info("** Saludos desde el logger **");

        Optional<String> optChallengeService = discoveryClient.getInstances("itachallenge-challenge")
                .stream()
                .findAny()
                .map(Object::toString);

        Optional<String> userService = discoveryClient.getInstances("itachallenge-user")
                .stream()
                .findAny()
                .map(Object::toString);


        log.info("~~~~~~~~~~~~~~~~~~~~~~");
        log.info("Scanning micros:");

        StringBuilder logMessage = new StringBuilder("Scanning micros:");

        if (userService.isPresent()) {
            logMessage.append(System.lineSeparator()).append("User service available");
        } else {
            logMessage.append(System.lineSeparator()).append(NO_SERVICE);
        }

        if (optChallengeService.isPresent()) {
            logMessage.append(System.lineSeparator()).append("Challenge service available");
        } else {
            logMessage.append(System.lineSeparator()).append(NO_SERVICE);
        }


        String logMessageStr = logMessage.toString();
        log.info(logMessageStr);


        log.info("~~~~~~~~~~~~~~~~~~~~~~");


        return "Hello from ITA Challenge!!!";
    }

    @GetMapping(path = "/challenges/{challengeId}")
    @Operation(
            operationId = "Get the information from a chosen challenge.",
            summary = "Get to see the Challenge level, its details and the available languages.",
            description = "Sending the ID Challenge through the URI to retrieve it from the database.",
            responses = {
                    @ApiResponse(responseCode = "200", content = {@Content(schema = @Schema(implementation = ChallengeDto.class), mediaType = "application/json")}),
                    @ApiResponse(responseCode = "400", description = "Malformed or invalid parameter(s)"),
                    @ApiResponse(responseCode = "404", description = "The Challenge with given Id was not found.")
            }
    )
    public Mono<ResponseEntity<ChallengeDto>> getOneChallenge(@PathVariable("challengeId") String id) {

        return challengeService.getChallengeById(id)
                .map(dto -> ResponseEntity.ok().body(dto));
    }

    @GetMapping("/challenges")
    @Operation(
            operationId = "Get only the challenges on a page.",
            summary = "Get to see challenges on a page and their levels, details and their available languages.",
            description = "Requesting the challenges for a page sending page number and the number of items per page through the URI from the database.",
            responses = {
                    @ApiResponse(responseCode = "200", content = {@Content(schema = @Schema(implementation = ChallengeDto.class), mediaType = "application/json")}),
                    @ApiResponse(responseCode = "400", description = "Missing or unexpected parameters")

            })

    public Mono<GenericResultDto<ChallengeDto>> getAllChallenges(
            @RequestParam(defaultValue = DEFAULT_OFFSET) @ValidGenericPattern(message = INVALID_PARAM) String offset,
            @RequestParam(defaultValue = DEFAULT_LIMIT) @ValidGenericPattern(pattern = LIMIT, message = INVALID_PARAM) String limit) {
        return challengeService.getAllChallenges(Integer.parseInt(offset), Integer.parseInt(limit));
    }

    @GetMapping("/challenges/byFilter")
    @Operation(
            operationId = "Get challenges on a page by FILTER (language, difficulty, or tags).",
            summary = "Get to see challenges on a page and their levels, details and their available languages by language and difficulty, language or difficulty.",
            description = "Requesting the challenges for a page sending page number and the number of items per page through the URI from the database.",
            responses = {
                    @ApiResponse(responseCode = "200", content = {@Content(schema = @Schema(implementation = ChallengeDto.class), mediaType = "application/json")}),
                    @ApiResponse(responseCode = "200", description = "The language with given Id was not found."),
                    @ApiResponse(responseCode = "400", description = "Missing or unexpected parameters"),
                    @ApiResponse(responseCode = "400", description = "Malformed UUID")
            })

    public Flux<GenericResultDto<ChallengeDto>> getChallengesByFilter(@ModelAttribute ChallengeFilterDto filter) {
        log.info("Entering in filter service with this filter:\n" + filter.toString());
        return challengeService.getChallengesByFilter(
                Optional.ofNullable(filter.getIdLanguage()),
                Optional.ofNullable(filter.getLevel()),
                Optional.ofNullable(filter.getTags()),
                filter.getOffset(),
                filter.getLimit()
        );
    }

    @GetMapping("/challenges/{challengeId}/related")
    @Operation(
            operationId = "Get 3 related challenges on the \"Relacionat\" tab of a Challenge detail by (language, difficulty, or tags).",
            summary = "Get to see 3 related challenges on a challenge detail page and their levels, details and their depending on the first language, difficulty and any tags.",
            description = "Requesting 3 related challenges for the challenge the user is actually looking at or working on.",
            responses = {
                    @ApiResponse(responseCode = "200", description = "Successfully retrieved related challenges",
                            content = {@Content(schema = @Schema(implementation = ChallengeDto.class), mediaType = "application/json")}),
                    @ApiResponse(responseCode = "204", description = "No related challenges found"),
                    @ApiResponse(responseCode = "404", description = "The Challenge with given Id was not found"),
                    @ApiResponse(responseCode = "400", description = "Malformed, missing or invalid parameters")
            })

    public Mono<ResponseEntity<GenericResultDto<ChallengeDto>>> getRelatedChallenges(@PathVariable String challengeId) {
        return challengeService.getRelatedChallenges(challengeId)
                .map(result -> {
                    if (result.getCount() == 0) {
                        return ResponseEntity.noContent().<GenericResultDto<ChallengeDto>>build();
                    }
                    return ResponseEntity.ok(result);
                });
    }

    @GetMapping("/solution/challenge/{idChallenge}/language/{idLanguage}")
    @Operation(
            operationId = "Get the solutions from a chosen challenge and language.",
            summary = "Get to see the Solution id, text and language.",
            description = "Sending the ID Challenge and ID Language through the URI to retrieve the Solution from the database.",
            responses = {
                    @ApiResponse(responseCode = "200", content = {@Content(schema = @Schema(implementation = GenericResultDto.class), mediaType = "application/json")}),
                    @ApiResponse(responseCode = "200", description = "Successful operation."),
                    @ApiResponse(responseCode = "400", description = "Malformed or invalid parameter(s)"),
                    @ApiResponse(responseCode = "404", description = "The Challenge with given Id was not found.")
            }
    )
    public Mono<GenericResultDto<SolutionDto>> getSolutions(@PathVariable("idChallenge") String
                                                                    idChallenge, @PathVariable("idLanguage") String idLanguage) {
        return challengeService.getSolutions(idChallenge, idLanguage);

    }

    @PostMapping("/solution")
    @Operation(
            operationId = "Add solution to a chosen chosen challenge.",
            summary = "Update the Challenge level, add accepted solution to the challenge.",
            description = "Sending the ID Challenge, ID Lenguage and the solution through the body URI to update it from the database.",
            responses = {
                    @ApiResponse(responseCode = "200", content = {@Content(schema = @Schema(implementation = SolutionDto.class), mediaType = "application/json")}),
                    @ApiResponse(responseCode = "200", description = "Successful operation.", content = {@Content(schema = @Schema())}),
                    @ApiResponse(responseCode = "400", description = "The solution cannot be null and the solution text cannot be empty.", content = {@Content(schema = @Schema())}),
                    @ApiResponse(responseCode = "400", description = "Malformed or invalid parameter(s)"),
                    @ApiResponse(responseCode = "404", description = "The Challenge with given Id was not found.")
            }
    )
    public Mono<Map<String, Object>> addSolution(@Valid @RequestBody SolutionDto solutionDto) {
        return challengeService.addSolution(solutionDto)
                .map(solution -> {
                    Map<String, Object> response = new HashMap<>();
                    response.put("uuid_challenge", solution.getIdChallenge());
                    response.put("uuid_language", solution.getIdLanguage());
                    response.put("solution_text", solution.getSolutionText());
                    return response;
                });
    }

    @PostMapping("/challenges")
    @Operation(
            operationId = "Add challenge.",
            summary = "Post a challenge providing the necessary data.",
            description = "Sending the title, description, difficulty level, language and solution, a new challenge document will be inserted in the database.",
            responses = {
                    @ApiResponse(responseCode = "200", content = {@Content(schema = @Schema(implementation = ChallengeCreateDto.class), mediaType = "application/json")}),
                    @ApiResponse(responseCode = "400", description = "Missing parameter(s)"),
            }
    )

    public Mono<ResponseEntity<ChallengeDto>> addChallenge(
            @Valid @RequestBody ChallengeCreateDto createFormDto,
            @RequestHeader(name = "Authorization", required = false) String authHeader) {

        return Mono.fromCallable(() -> challengeJwtFacade.getUserUuIdFromAuthenticationHeader(authHeader))
                .onErrorMap(JwtException.class, e -> new BadRequestException(e.getMessage()))
                .flatMap(userId -> challengeService.addChallenge(createFormDto))
                .doOnError(error -> log.error("Error adding challenge: {}", error.getMessage()))
                .map(ResponseEntity::ok);
    }
    @GetMapping("/version")
    @Operation(
            summary = "Get Application Version",
            description = "Retrieve the version of the application.",
            responses = {
                    @ApiResponse(
                            responseCode = "200",
                            description = "Successful response with the application version and name.",
                            content = @Content(schema = @Schema(implementation = Map.class))
                    )
            }
    )
    public Mono<ResponseEntity<Map<String, String>>> getVersion() {
        Map<String, String> response = new HashMap<>();
        response.put("application_name", appName);
        response.put("version", version);
        return Mono.just(ResponseEntity.ok(response));
    }

    @DeleteMapping(path = "/challenges/{challengeId}")
    @Operation(
            operationId = "deleteChallenge",
            summary = "Delete a challenge",
            description = "Deletes the challenge identified by the provided UUID.",
            responses = {
                    @ApiResponse(
                            responseCode = "200",
                            description = "Challenge deleted successfully",
                            content = @Content(schema = @Schema(implementation = DeleteResponseDto.class))
                    ),
                    @ApiResponse(
                            responseCode = "400",
                            description = "Malformed or invalid parameter(s)"
                    ),
                    @ApiResponse(
                            responseCode = "404",
                            description = "The challenge with the given ID was not found."
                    )
            }
    )
    public Mono<ResponseEntity<DeleteResponseDto>> deleteChallenge(
            @PathVariable String challengeId) {

        return challengeService.deleteChallengeById(challengeId)
                .map(ResponseEntity::ok);
    }

    @PostMapping("/challenges/{challengeId}/bookmarks")
    @Operation(
            operationId = "Add a challenge to User's bookmarks.",
            summary = "Add a challenge to bookmarks.",
            description = "The ID Challenge sent through the URI is added to the user's bookmarks. User Id is determined from the headers.",
            responses = {
                    @ApiResponse(responseCode = "200", content = {@Content(schema = @Schema(implementation = FavoriteDto.class), mediaType = "application/json")}),
                    @ApiResponse(responseCode = "400", description = "Missing or invalid authorization header."),
                    @ApiResponse(responseCode = "404", description = "The Challenge with given Id was not found."),
                    @ApiResponse(responseCode = "500", description = "Internal Server Error")
            }
    )
    public Mono<ResponseEntity<BookmarkDto>> addChallengeToBookmarks(
            @PathVariable String challengeId,
            @RequestHeader(name = "Authorization", required = false) String authHeader) {
        return Mono.fromCallable(() -> challengeJwtFacade.getUserUuIdFromAuthenticationHeader(authHeader))
                .onErrorMap(JwtException.class, e -> new BadRequestException(e.getMessage()))
                .flatMap(userId -> challengeService.addChallengeToBookmarks(challengeId, userId))
                .doOnError(error -> log.error("Error adding challenge to bookmarks: {}", error.getMessage()))
                .map(ResponseEntity::ok);
    }

    @PutMapping("/challenge/{challengeId}/update")
    @Operation(
            operationId = "Updates an existing challenge.",
            summary = "Updates information of a challenge.",
            description = "Allows to update any information contained in a challenge, providing ChallengeId and new information.",
            responses = {
                    @ApiResponse(responseCode = "200", content = {@Content(schema = @Schema(implementation = ChallengeDto.class), mediaType = "application/json")}),
                    @ApiResponse(responseCode = "400", description = "Missing or invalid authorization header."),
                    @ApiResponse(responseCode = "403", description = "User is not authorized to perform this action."),
                    @ApiResponse(responseCode = "404", description = "The Challenge with given Id was not found."),
                    @ApiResponse(responseCode = "500", description = "Internal Server Error")
            }
    )
   public Mono<ResponseEntity<ChallengeDto>> updateChallenge(
           @PathVariable String challengeId,
           @Valid @RequestBody ChallengeCreateDto challengeFormDto,
           @RequestHeader(name = "Authorization", required = false) String authHeader) {
       return Mono.fromCallable(() -> challengeJwtFacade.getUserUuIdFromAuthenticationHeader(authHeader))
               .onErrorMap(JwtException.class, e -> new BadRequestException(e.getMessage()))
               .flatMap(userId -> challengeService.updateChallenge(challengeId, challengeFormDto))
               .map(ResponseEntity::ok)
               .doOnError(error -> log.error("Error updating challenge: {}", error.getMessage()));
   }

    @DeleteMapping("/challenges/{challengeId}/bookmarks")
    @Operation(
            operationId = "Remove a challenge from the User's bookmarks.",
            summary = "Remove a challenge from bookmarks.",
            description = "The ID Challenge sent through the URI is removed from the user's bookmarks. User Id is determined from the headers.",
            responses = {
                    @ApiResponse(responseCode = "200", content = {@Content(schema = @Schema(implementation = FavoriteDto.class), mediaType = "application/json")}),
                    @ApiResponse(responseCode = "400", description = "Missing or invalid authorization header."),
                    @ApiResponse(responseCode = "404", description = "The Challenge with given Id was not found."),
                    @ApiResponse(responseCode = "500", description = "Internal Server Error")
            }
    )
    public Mono<ResponseEntity<BookmarkDto>> removeChallengeFromBookmarks(
            @PathVariable String challengeId,
            @RequestHeader(name = "Authorization", required = false) String authHeader) {
        return Mono.fromCallable(() -> challengeJwtFacade.getUserUuIdFromAuthenticationHeader(authHeader))
                .onErrorMap(JwtException.class, e -> new BadRequestException(e.getMessage()))
                .flatMap(userId -> challengeService.removeChallengeFromBookmarks(challengeId, userId))
                .doOnError(error -> log.error("Error removing challenge with id {} from bookmarks: {}", challengeId, error.getMessage()))
                .map(ResponseEntity::ok);
    }

}

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/controller/ChallengeController.java:ChallengeController.<init>
// Node: elements
// Node: getInstances
// Node: findAny
// Node: StringBuilder
// Node: isPresent
// Node: append
// Node: lineSeparator
// Node: getOneChallenge
// Node: PathVariable
// Node: RequestParam
// Node: parseInt
// Node: FILTER
// Node: noContent
// Node: getIdChallenge
// Node: deleteChallenge
// Node: deleteChallengeById
package com.itachallenge.challenge.controller.submission;

import com.itachallenge.challenge.dto.submission.SubmissionActionRequestDto;
import com.itachallenge.challenge.dto.submission.SubmissionDto;
import com.itachallenge.submission.service.SubmissionService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.enums.ParameterIn;
import io.swagger.v3.oas.annotations.media.ArraySchema;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Flux;
import com.itachallenge.challenge.dto.submission.SubmissionActionResponseDto;
import org.springframework.http.ResponseEntity;
import reactor.core.publisher.Mono;
import jakarta.validation.Valid;




@RestController
@Validated
@RequiredArgsConstructor
@RequestMapping("/itachallenge/api/v1/users/{userId}/submissions")
public class SubmissionController {

    private static final Logger log = LoggerFactory.getLogger(SubmissionController.class);
    private final SubmissionService submissionService;

    @GetMapping
    @Operation(
            summary = "Get submissions by userId",
            description = "Returns all submissions for the given user. Empty array if none.",
            parameters = {
                    @Parameter(
                            name = "userId",
                            in = ParameterIn.PATH,
                            required = true,
                            description = "User UUID"
                    )
            },
            responses = {
                    @ApiResponse(
                            responseCode = "200",
                            description = "OK – empty array if none",
                            content = @Content(
                                    mediaType = "application/json",
                                    array = @ArraySchema(schema = @Schema(implementation = SubmissionDto.class))
                            )
                    ),
                    @ApiResponse(responseCode = "400", description = "Malformed UUID")
            }
    )
    public Flux<SubmissionDto> getAllSubmissionsByUser(@PathVariable String userId) {
        return submissionService.getAllSubmissionsByUser(userId);
    }

    @PostMapping
    @Operation(
            summary = "Create or update a submission",
            description = "Creates or updates a user submission depending on the action (SAVE, SUBMIT, GIVE_UP).",
            parameters = {
                    @Parameter(
                            name = "userId",
                            in = ParameterIn.PATH,
                            required = true,
                            description = "User UUID"
                    )
            },
            responses = {
                    @ApiResponse(
                            responseCode = "200",
                            description = "OK",
                            content = @Content(
                                    mediaType = "application/json",
                                    schema = @Schema(implementation = SubmissionActionResponseDto.class)
                            )
                    ),
                    @ApiResponse(responseCode = "400", description = "Invalid UUID or action"),
                    @ApiResponse(responseCode = "409", description = "Submission already completed"),
                    @ApiResponse(responseCode = "500", description = "Unexpected error")
            }
    )
    public Mono<ResponseEntity<SubmissionActionResponseDto>> createOrUpdateSubmission(
            @PathVariable String userId,
            @Valid @RequestBody SubmissionActionRequestDto request
    ) {
        return submissionService.processSubmissionAction(userId, request)
                .map(ResponseEntity::ok);
    }



}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/controller/submission/SubmissionController.java:SubmissionController.<init>
// Node: ArraySchema
// Node: createOrUpdateSubmission
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

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/service/LanguageServiceImpl.java:LanguageServiceImpl.<init>
// Node: Cacheable
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

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/service/ChallengeServiceImpl.java:ChallengeServiceImpl.<init>
// Node: CacheEvict
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

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/service/FavoriteServiceImpl.java:FavoriteServiceImpl.<init>
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


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/service/TagServiceImpl.java:TagServiceImpl.<init>
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

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/service/ResourceServiceImpl.java:ResourceServiceImpl.<init>
// Node: ResourceServiceImpl
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


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/service/UserServiceImpl.java:UserServiceImpl.<init>
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


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/validator/GenericPatternValidator.java:GenericPatternValidator.<init>
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


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/config/PropertiesConfig.java:PropertiesConfig.<init>
package com.itachallenge.challenge.config;

import org.springframework.cache.Cache;
import org.springframework.cache.CacheManager;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.cache.concurrent.ConcurrentMapCache;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.Collection;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;
import java.util.concurrent.TimeUnit;

@Configuration
@EnableCaching
public class CacheConfig {

    @Bean
    public CacheManager cacheManager() {
        return new CustomCacheManager();
    }

    static class CustomCacheManager implements CacheManager {

        private final ConcurrentMap<String, Cache> cacheMap = new ConcurrentHashMap<>();

        @Override
        public Cache getCache(String name) {
            return cacheMap.computeIfAbsent(name, CustomCache::new);
        }

        @Override
        public Collection<String> getCacheNames() {
            return cacheMap.keySet();
        }
    }

    static class CustomCache extends ConcurrentMapCache {

        private final ConcurrentMap<Object, Long> expirationMap = new ConcurrentHashMap<>();
        private final long expirationTime = TimeUnit.MINUTES.toMillis(10); // Set cache duration here

        public CustomCache(String name) {
            super(name);
        }

        @Override
        public void put(Object key, Object value) {
            super.put(key, value);
            expirationMap.put(key, System.currentTimeMillis() + expirationTime);
        }

        @Override
        public ValueWrapper get(Object key) {
            if (isExpired(key)) {
                evict(key);
                return null;
            }
            return super.get(key);
        }

        @Override
        public void evict(Object key) {
            super.evict(key);
            expirationMap.remove(key);
        }

        private boolean isExpired(Object key) {
            Long expirationTime2 = expirationMap.get(key);
            return expirationTime2 == null || System.currentTimeMillis() > expirationTime2;
        }
    }
}

package com.itachallenge.challenge.config;

import com.mongodb.reactivestreams.client.MongoClient;
import io.mongock.driver.mongodb.reactive.driver.MongoReactiveDriver;
import io.mongock.runner.springboot.MongockSpringboot;
import io.mongock.runner.springboot.base.MongockInitializingBeanRunner;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.ApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;

@Configuration
@Profile("mongock")
public class MongockConfig {

    @Value("${mongock.migration-scan-package}")
    private String migrationScanPackage;

    @Value("${mongock.transactionEnabled}")
    private boolean transactionEnabled;

    @Bean
    public MongockInitializingBeanRunner getBuilder(MongoClient mongoClient,
                                                    ApplicationContext context) {
        return MongockSpringboot.builder()
                .setDriver(MongoReactiveDriver.withDefaultLock(mongoClient, "challenges"))
                .addMigrationScanPackage(migrationScanPackage)
                .setSpringContext(context)
                .setTransactionEnabled(transactionEnabled)
                .buildInitializingBeanRunner();
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/config/MongockConfig.java:MongockConfig.<init>
// Node: Profile
// Node: getBuilder
// Node: setDriver
// Node: withDefaultLock
// Node: addMigrationScanPackage
// Node: setSpringContext
// Node: setTransactionEnabled
// Node: buildInitializingBeanRunner
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

// Node: timeoutTest
// Node: mutate
// Node: createException
package com.itachallenge.challenge.config;

import com.mongodb.reactivestreams.client.MongoClient;
import io.mongock.driver.mongodb.reactive.driver.MongoReactiveDriver;
import io.mongock.runner.springboot.MongockSpringboot;
import io.mongock.runner.springboot.base.MongockInitializingBeanRunner;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.ApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;

@Configuration
@Profile("mongockTest")
public class MongockConfig {

    @Value("${mongock.migration-scan-package}")
    private String migrationScanPackage;

    @Value("${mongock.transactionEnabled}")
    private boolean transactionEnabled;

    @Bean
    public MongockInitializingBeanRunner getBuilder(MongoClient mongoClient,
                                                    ApplicationContext context) {
        return MongockSpringboot.builder()
                .setDriver(MongoReactiveDriver.withDefaultLock(mongoClient, "challenges"))
                .addMigrationScanPackage(migrationScanPackage)
                .setSpringContext(context)
                .setTransactionEnabled(transactionEnabled)
                .buildInitializingBeanRunner();
    }
}

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/challenge/config/MongockConfig.java:MongockConfig.<init>
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

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-auth/src/main/java/com/itachallenge/auth/controller/AuthController.java:AuthController.<init>
// Node: AuthController
// Node: authenticateWithGithub
// Node: getUserDetailsFromGithubUsername
// Node: logout
// Node: getNewRole
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


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-auth/src/main/java/com/itachallenge/auth/service/AuthService.java:AuthService.<init>
// Node: AuthService
// Node: createRequestBody
// Node: createSuccessResult
// Node: createErrorResult
// Node: handleGithubApiError
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


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-auth/src/main/java/com/itachallenge/auth/service/UserService.java:UserService.<init>
// Node: UserService
package com.itachallenge.auth.dto;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "Payload to request a temporary role switch.")
public class SwitchRoleRequest {

    @Schema(
            description = "The new role to switch to. Allowed values: ADMIN, USER.",
            example = "ADMIN",
            required = true
    )
    private String newRole;

    public SwitchRoleRequest() {
    }

    public SwitchRoleRequest(String newRole) {
        this.newRole = newRole;
    }

    public String getNewRole() {
        return newRole;
    }

    public void setNewRole(String newRole) {
        this.newRole = newRole;
    }
}

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-auth/src/main/java/com/itachallenge/auth/dto/SwitchRoleRequest.java:SwitchRoleRequest.<init>
package com.itachallenge.mock.controller;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Mono;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping(value = "/itachallenge/api/v1/mock")
public class MockController {
    @Value("${spring.application.version}")
    private String version;

    @Value("${spring.application.name}")
    private String appName;

    @RequestMapping(value = "/test")
    public String test() {
        return "Hello ITAchallenge-Mock  ;) !!!";
    }

    @GetMapping(value="/version")
    public Mono<ResponseEntity<Map<String, String>>> getVersion() {
        Map<String, String> response = new HashMap<>();
        response.put("application_name", appName);
        response.put("version", version);
        return Mono.just(ResponseEntity.ok(response));
    }

}



// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-mock/src/main/java/com/itachallenge/mock/controller/MockController.java:MockController.<init>
