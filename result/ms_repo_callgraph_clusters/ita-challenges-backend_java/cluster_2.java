// Cluster 2

// Node: getUserUuIdFromAuthenticationHeader
// Node: getMessage
// Node: JwtException
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

// Node: get
// Node: toString
// Node: isEqualTo
// Node: RuntimeException
// Node: getProperty
// Node: when
// Node: thenReturn
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

// Node: shouldReturnCorrectAppVersion
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


// Node: shouldGetSwaggerChallengeDocsStr
// Node: shouldGetSwaggerAuthDocsStr
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


// Node: uri
// Node: statusCode
// Node: equals
// Node: just
// Node: is5xxServerError
// Node: error
// Node: verify
// Node: value
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


// Node: hasSize
// Node: any
// Node: Exception
package com.itachallenge.userinteraction.repository.bookmark;

import com.itachallenge.userinteraction.document.bookmark.BookmarkDocument;
import org.springframework.data.mongodb.repository.ReactiveMongoRepository;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.UUID;

public interface BookmarkRepository extends ReactiveMongoRepository<BookmarkDocument, UUID> {
    Flux<BookmarkDocument> findByUserId(UUID userId);
    Mono<BookmarkDocument> findByUserIdAndChallengeId(UUID userId, UUID challengeId);
    Mono<Void> deleteByUserIdAndChallengeId(UUID userId, UUID challengeId);
    Mono<Boolean> existsByUserIdAndChallengeId(UUID userId, UUID challengeId);
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/userinteraction/repository/bookmark/BookmarkRepository.java:BookmarkRepository.<init>
// Node: findByUserId
// Node: findByUserIdAndChallengeId
// Node: deleteByUserIdAndChallengeId
// Node: existsByUserIdAndChallengeId
package com.itachallenge.userinteraction.repository.favorite;

import com.itachallenge.userinteraction.document.favorite.FavoriteDocument;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.UUID;

import org.springframework.data.mongodb.repository.ReactiveMongoRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface FavoriteRepository extends ReactiveMongoRepository<FavoriteDocument, UUID> {
    Flux<FavoriteDocument> findByUserId(UUID userId);
    Mono<FavoriteDocument> findByUserIdAndChallengeId(UUID userId, UUID challengeId);
    Mono<Void> deleteByUserIdAndChallengeId(UUID userId, UUID challengeId);
    Mono<Boolean> existsByUserIdAndChallengeId(UUID userId, UUID challengeId);

}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/userinteraction/repository/favorite/FavoriteRepository.java:FavoriteRepository.<init>
// Node: getUserBookmarks
// Node: existsById
package com.itachallenge.userinteraction.service.bookmark;

import reactor.core.publisher.Mono;

import java.util.Set;
import java.util.UUID;

public interface BookmarkService {
    Mono<Set<UUID>> getUserBookmarks(String userId);
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/userinteraction/service/bookmark/BookmarkService.java:BookmarkService.<init>
package com.itachallenge.userinteraction.service.favorite;

import reactor.core.publisher.Mono;

import java.util.Set;
import java.util.UUID;

public interface FavoriteService {
    Mono<Boolean> addChallengeToFavorites(String userId, String challengeId);

    Mono<Set<UUID>> getUserFavorites(String userId);

    Mono<Boolean> deleteChallengeFromFavorites(String userId, String challengeId);
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/userinteraction/service/favorite/FavoriteService.java:FavoriteService.<init>
// Node: addChallengeToFavorites
// Node: getUserFavorites
// Node: deleteChallengeFromFavorites
// Node: findById
// Node: randomUUID
// Node: delete
// Node: createUser
// Node: getUser
// Node: header
// Node: addChallengeToBookmarks
// Node: deleteChallengeFromBookmarks
package com.itachallenge.user.repository;

import com.itachallenge.user.document.UserDocument;
import org.springframework.data.mongodb.repository.ReactiveMongoRepository;
import org.springframework.stereotype.Repository;
import reactor.core.publisher.Mono;

import java.util.UUID;

@Repository
public interface UserRepository extends ReactiveMongoRepository<UserDocument, UUID> {

    Mono<UserDocument> findByUsername(String username);

}




// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/repository/UserRepository.java:UserRepository.<init>
// Node: findByUsername
package com.itachallenge.user.service;

import com.itachallenge.user.dto.AdminCreateUserRequestDto;
import com.itachallenge.user.dto.AdminCreateUserResponseDto;
import reactor.core.publisher.Mono;

public interface IAdminCreateUserService {

    Mono<AdminCreateUserResponseDto> createUser(AdminCreateUserRequestDto request);

}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/service/IAdminCreateUserService.java:IAdminCreateUserService.<init>
package com.itachallenge.user.service;

import com.itachallenge.user.document.UserDocument;
import reactor.core.publisher.Mono;

public interface UserService {
    Mono<UserDocument> getUser(String githubUsername);

    Mono<Boolean> addChallengeToBookmarks(String userId, String challengeId);

    Mono<Boolean> deleteChallengeFromBookmarks(String userId, String challengeId);

    Mono<UserDocument> getUserById(String userId);
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/service/UserService.java:UserService.<init>
// Node: getUserById
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


// Node: BookmarkDocument
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


// Node: getUserBookmarks_WhenUserHasNoBookmarks_ReturnsEmptySet
// Node: empty
// Node: times
// Node: getUserBookmarks_WhenUserExistsWithFavorites_ReturnsBookmarks
// Node: getUserBookmarks_WhenUserNotFound_ThrowsNotFoundException
// Node: expectErrorMatches
// Node: getUserBookmarks_WhenInvalidUUID_ThrowsBadUUIDException
// Node: getUserBookmarks_WhenRepositoryError_PropagatesError
package com.itachallenge.userinteraction.service.favorite;

import com.itachallenge.user.document.UserDocument;
import com.itachallenge.user.exception.BadUUIDException;
import com.itachallenge.user.exception.NotFoundException;
import com.itachallenge.user.repository.UserRepository;
import com.itachallenge.userinteraction.document.favorite.FavoriteDocument;
import com.itachallenge.userinteraction.repository.favorite.FavoriteRepository;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

import java.util.Set;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.mockito.Mockito.*;

class FavoriteServiceImplTest {

    @Mock
    private FavoriteRepository favoriteRepository;

    @Mock
    private UserRepository userRepository;

    @InjectMocks
    private FavoriteServiceImpl favoriteService;

    private AutoCloseable mocks;

    private static final String USER_NOT_FOUND_WITH_ID = "User not found with id: ";

    @BeforeEach
    void setUp() {
        mocks = MockitoAnnotations.openMocks(this);
        favoriteService = new FavoriteServiceImpl(favoriteRepository, userRepository);
    }

    @AfterEach
    void tearDown() throws Exception {
        if (mocks != null) mocks.close();
    }

    @Test
    void addChallengeToFavorites_ShouldReturnTrue_WhenFavoriteDoesNotExist() {
        UUID userId = UUID.randomUUID();
        UUID challengeId = UUID.randomUUID();
        UserDocument user = new UserDocument(userId, "testUser", null, 0);

        when(userRepository.findById(userId)).thenReturn(Mono.just(user));
        when(favoriteRepository.existsByUserIdAndChallengeId(userId, challengeId))
                .thenReturn(Mono.just(false));
        when(favoriteRepository.save(any(FavoriteDocument.class)))
                .thenReturn(Mono.just(new FavoriteDocument()));

        StepVerifier.create(favoriteService.addChallengeToFavorites(userId.toString(), challengeId.toString()))
                .expectNext(true)
                .verifyComplete();

        verify(userRepository, times(1)).findById(userId);
        verify(favoriteRepository, times(1)).existsByUserIdAndChallengeId(userId, challengeId);
        verify(favoriteRepository, times(1)).save(any(FavoriteDocument.class));
        verify(userRepository, never()).save(any());
    }

    @Test
    void addChallengeToFavorites_ShouldReturnFalse_WhenFavoriteAlreadyExists() {
        UUID challengeId = UUID.randomUUID();
        UUID userId = UUID.randomUUID();
        UserDocument user = new UserDocument(userId, "testUser", null, 0);

        when(userRepository.findById(userId)).thenReturn(Mono.just(user));
        when(favoriteRepository.existsByUserIdAndChallengeId(userId, challengeId))
                .thenReturn(Mono.just(true));

        StepVerifier.create(favoriteService.addChallengeToFavorites(userId.toString(), challengeId.toString()))
                .expectNext(false)
                .verifyComplete();

        verify(userRepository, times(1)).findById(userId);
        verify(favoriteRepository, times(1)).existsByUserIdAndChallengeId(userId, challengeId);
        verify(favoriteRepository, never()).save(any());
    }

    @Test
    void addChallengeToFavorites_ShouldThrowNotFoundException_WhenUserNotFound() {
        UUID userId = UUID.randomUUID();
        UUID challengeId = UUID.randomUUID();

        when(userRepository.findById(any(UUID.class))).thenReturn(Mono.empty());

        StepVerifier.create(favoriteService.addChallengeToFavorites(userId.toString(), challengeId.toString()))
                .expectErrorSatisfies(throwable -> {
                    assertInstanceOf(NotFoundException.class, throwable);
                    assertEquals("User not found", throwable.getMessage());
                })
                .verify();

        verify(userRepository, times(1)).findById(userId);
        verify(favoriteRepository, never()).existsByUserIdAndChallengeId(any(), any());
        verify(favoriteRepository, never()).save(any());
        verify(userRepository, never()).save(any());
    }

    @Test
    void addChallengeToFavorites_ShouldThrowBadRequestException_WhenUserUuidIsNull() {
        String invalidUserId = null;
        String validChallengeId = UUID.randomUUID().toString();

        StepVerifier.create(favoriteService.addChallengeToFavorites(invalidUserId, validChallengeId))
                .expectErrorSatisfies(throwable -> {
                    assertInstanceOf(BadUUIDException.class, throwable);
                    assertEquals("Invalid ID format", throwable.getMessage());
                })
                .verify();

        verify(userRepository, never()).findById(Mockito.<UUID>any());
        verify(favoriteRepository, never()).existsByUserIdAndChallengeId(any(), any());
        verify(favoriteRepository, never()).save(any());
        verify(userRepository, never()).save(any());
    }

    @Test
    void addChallengeToFavorites_ShouldThrowBadRequestException_WhenChallengeUuidIsNull() {
        String validUserId = UUID.randomUUID().toString();
        String invalidChallengeId = null;

        StepVerifier.create(favoriteService.addChallengeToFavorites(validUserId, invalidChallengeId))
                .expectErrorSatisfies(throwable -> {
                    assertInstanceOf(BadUUIDException.class, throwable);
                    assertEquals("Invalid ID format", throwable.getMessage());
                })
                .verify();

        verify(userRepository, never()).findById(Mockito.<UUID>any());
        verify(favoriteRepository, never()).existsByUserIdAndChallengeId(any(), any());
        verify(favoriteRepository, never()).save(any());
        verify(userRepository, never()).save(any());
    }

    @Test
    void addChallengeToFavorites_ShouldThrowBadRequestException_WhenUserUuidIsNotValid() {
        String invalidUserId = "invalidUuid";
        String validChallengeId = UUID.randomUUID().toString();

        StepVerifier.create(favoriteService.addChallengeToFavorites(invalidUserId, validChallengeId))
                .expectErrorSatisfies(throwable -> {
                    assertInstanceOf(BadUUIDException.class, throwable);
                    assertEquals("Invalid ID format", throwable.getMessage());
                })
                .verify();

        verify(userRepository, never()).findById(Mockito.<UUID>any());
        verify(favoriteRepository, never()).existsByUserIdAndChallengeId(any(), any());
        verify(favoriteRepository, never()).save(any());
        verify(userRepository, never()).save(any());
    }

    @Test
    void addChallengeToFavorites_ShouldThrowBadUUIDException_WhenChallengeUuidIsNotValid() {
        String validUserId = UUID.randomUUID().toString();
        String invalidChallengeId = "invalidUuid";

        StepVerifier.create(favoriteService.addChallengeToFavorites(validUserId, invalidChallengeId))
                .expectErrorSatisfies(throwable -> {
                    assertInstanceOf(BadUUIDException.class, throwable);
                    assertEquals("Invalid ID format", throwable.getMessage());
                })
                .verify();

        verify(userRepository, never()).findById(Mockito.<UUID>any());
        verify(favoriteRepository, never()).existsByUserIdAndChallengeId(any(), any());
        verify(favoriteRepository, never()).save(any());
        verify(userRepository, never()).save(any());
    }

    @Test
    @DisplayName("getUserFavorites returns an empty set when the user exists but has no favorites")
    void getUserFavorites_WhenUserHasNoFavorites_ReturnsEmptySet() {
        UUID userId = UUID.randomUUID();

        when(userRepository.existsById(userId)).thenReturn(Mono.just(true));
        when(favoriteRepository.findByUserId(userId)).thenReturn(Flux.empty());

        StepVerifier.create(favoriteService.getUserFavorites(userId.toString()))
                .expectNextMatches(Set::isEmpty)
                .verifyComplete();

        verify(userRepository, times(1)).existsById(userId);
        verify(favoriteRepository, times(1)).findByUserId(userId);
    }

    @Test
    @DisplayName("getUserFavorites returns favorites when the user exists")
    void getUserFavorites_WhenUserExistsWithFavorites_ReturnsFavorites() {
        UUID userId = UUID.randomUUID();
        UUID challengeId1 = UUID.randomUUID();
        UUID challengeId2 = UUID.randomUUID();

        FavoriteDocument fav1 = FavoriteDocument.builder()
                .uuid(UUID.randomUUID())
                .userId(userId)
                .challengeId(challengeId1)
                .build();
        FavoriteDocument fav2 = FavoriteDocument.builder()
                .uuid(UUID.randomUUID())
                .userId(userId)
                .challengeId(challengeId2)
                .build();

        when(userRepository.existsById(userId)).thenReturn(Mono.just(true));
        when(favoriteRepository.findByUserId(userId)).thenReturn(Flux.just(fav1, fav2));

        StepVerifier.create(favoriteService.getUserFavorites(userId.toString()))
                .expectNextMatches(favorites -> favorites.contains(challengeId1) && favorites.contains(challengeId2))
                .verifyComplete();

        verify(userRepository, times(1)).existsById(userId);
        verify(favoriteRepository, times(1)).findByUserId(userId);
    }

    @Test
    @DisplayName("getUserFavorites throws NotFoundException when the user does not exist")
    void getUserFavorites_WhenUserNotFound_ThrowsNotFoundException() {
        UUID userId = UUID.randomUUID();

        when(userRepository.existsById(userId)).thenReturn(Mono.just(false));

        StepVerifier.create(favoriteService.getUserFavorites(userId.toString()))
                .expectErrorMatches(error ->
                        error instanceof NotFoundException &&
                                error.getMessage().equals(USER_NOT_FOUND_WITH_ID + userId))
                .verify();

        verify(userRepository, times(1)).existsById(userId);
        verify(favoriteRepository, times(0)).findByUserId(userId);
    }

    @Test
    @DisplayName("getUserFavorites throws BadUUIDException when the UUID format is invalid")
    void getUserFavorites_WhenInvalidUUID_ThrowsBadUUIDException() {
        String invalidUUID = "invalid-uuid";

        StepVerifier.create(favoriteService.getUserFavorites(invalidUUID))
                .expectErrorMatches(error ->
                        error instanceof BadUUIDException &&
                                error.getMessage().equals("Invalid ID format"))
                .verify();

        verify(userRepository, times(0)).existsById((UUID) any());
        verify(favoriteRepository, times(0)).findByUserId(any());
    }

    @Test
    @DisplayName("getUserFavorites propagates repository errors correctly")
    void getUserFavorites_WhenRepositoryError_PropagatesError() {
        UUID userId = UUID.randomUUID();

        when(userRepository.existsById(userId)).thenReturn(Mono.just(true));
        when(favoriteRepository.findByUserId(userId)).thenReturn(Flux.error(new RuntimeException("DB error")));

        StepVerifier.create(favoriteService.getUserFavorites(userId.toString()))
                .expectErrorMatches(error ->
                        error instanceof RuntimeException &&
                                error.getMessage().equals("DB error"))
                .verify();

        verify(userRepository, times(1)).existsById(userId);
        verify(favoriteRepository, times(1)).findByUserId(userId);
    }

    @Test
    void deleteChallengeFromFavorites_ShouldThrowNotFoundException_WhenUserNotFound() {

        when(userRepository.findById(any(UUID.class))).thenReturn(Mono.empty());

        StepVerifier.create(favoriteService.deleteChallengeFromFavorites(UUID.randomUUID().toString(), UUID.randomUUID().toString()))
                .expectErrorSatisfies(throwable -> {
                    assertInstanceOf(NotFoundException.class, throwable);
                    assertEquals("User not found", throwable.getMessage());
                })
                .verify();

        verify(userRepository, times(1)).findById(any(UUID.class));
        verify(userRepository, times(0)).save(any());
    }

    @Test
    void deleteChallengeFromFavorites_ShouldThrowBadRequestException_WhenUserUuidIsNull() {
        StepVerifier.create(favoriteService.deleteChallengeFromFavorites(null, UUID.randomUUID().toString()))
                .expectErrorSatisfies(throwable -> {
                    assertInstanceOf(BadUUIDException.class, throwable);
                    assertEquals("Invalid ID format", throwable.getMessage());
                })
                .verify();

        verify(userRepository, times(0)).findById(any(UUID.class));
        verify(userRepository, times(0)).save(any());
    }

    @Test
    void deleteChallengeFromFavorites_ShouldThrowBadRequestException_WhenChallengeUuidIsNull() {
        StepVerifier.create(favoriteService.deleteChallengeFromFavorites(UUID.randomUUID().toString(), null))
                .expectErrorSatisfies(throwable -> {
                    assertInstanceOf(BadUUIDException.class, throwable);
                    assertEquals("Invalid ID format", throwable.getMessage());
                })
                .verify();

        verify(userRepository, times(0)).findById(any(UUID.class));
        verify(userRepository, times(0)).save(any());
    }

    @Test
    void deleteChallengeFromFavorites_ShouldThrowBadRequestException_WhenUserUuidIsNotValid() {
        StepVerifier.create(favoriteService.deleteChallengeFromFavorites("invalidUuid", UUID.randomUUID().toString()))
                .expectErrorSatisfies(throwable -> {
                    assertInstanceOf(BadUUIDException.class, throwable);
                    assertEquals("Invalid ID format", throwable.getMessage());
                })
                .verify();

        verify(userRepository, times(0)).findById(any(UUID.class));
        verify(userRepository, times(0)).save(any());
    }

    @Test
    void deleteChallengeFromFavorites_ShouldThrowBadRequestException_WhenChallengeUuidIsNotValid() {
        StepVerifier.create(favoriteService.deleteChallengeFromFavorites(UUID.randomUUID().toString(), "invalidUuid"))
                .expectErrorSatisfies(throwable -> {
                    assertInstanceOf(BadUUIDException.class, throwable);
                    assertEquals("Invalid ID format", throwable.getMessage());
                })
                .verify();

        verify(userRepository, times(0)).findById(any(UUID.class));
        verify(userRepository, times(0)).save(any());
    }

    @Test
    void deleteChallengeFromFavorites_ShouldReturnFalse_WhenFavoriteDoesNotExist() {
        UUID userId = UUID.randomUUID();
        UUID challengeId = UUID.randomUUID();
        UserDocument user = new UserDocument(userId, "testUser", null, 0);

        when(userRepository.findById(userId)).thenReturn(Mono.just(user));
        when(favoriteRepository.findByUserIdAndChallengeId(any(UUID.class), any(UUID.class)))
                .thenReturn(Mono.empty());

        StepVerifier.create(favoriteService.deleteChallengeFromFavorites(userId.toString(), challengeId.toString()))
                .expectNext(false)
                .verifyComplete();

        verify(userRepository).findById(userId);
        verify(favoriteRepository).findByUserIdAndChallengeId(any(UUID.class), any(UUID.class));
        verify(favoriteRepository, never()).delete(any());
    }

    @Test
    void deleteChallengeFromFavorites_ShouldReturnTrue_WhenFavoriteAlreadyExists() {
        // Arrange
        UUID userId = UUID.randomUUID();
        UUID challengeId = UUID.randomUUID();
        UserDocument user = new UserDocument(userId, "testUser", null, 0);
        FavoriteDocument favorite = FavoriteDocument.builder()
                .uuid(UUID.randomUUID())
                .userId(userId)
                .challengeId(challengeId)
                .build();

        when(userRepository.findById(userId)).thenReturn(Mono.just(user));
        when(favoriteRepository.findByUserIdAndChallengeId(userId, challengeId))
                .thenReturn(Mono.just(favorite));
        when(favoriteRepository.delete(any(FavoriteDocument.class))).thenReturn(Mono.empty());

        // Act & Assert
        StepVerifier.create(favoriteService.deleteChallengeFromFavorites(userId.toString(), challengeId.toString()))
                .expectNext(true)
                .verifyComplete();

        // Verify
        verify(userRepository).findById(userId);
        verify(favoriteRepository).findByUserIdAndChallengeId(userId, challengeId);
        verify(favoriteRepository).delete(favorite);
    }
}


// Node: addChallengeToFavorites_ShouldReturnTrue_WhenFavoriteDoesNotExist
// Node: UserDocument
// Node: never
// Node: addChallengeToFavorites_ShouldReturnFalse_WhenFavoriteAlreadyExists
// Node: addChallengeToFavorites_ShouldThrowNotFoundException_WhenUserNotFound
// Node: expectErrorSatisfies
// Node: assertInstanceOf
// Node: addChallengeToFavorites_ShouldThrowBadRequestException_WhenUserUuidIsNull
// Node: addChallengeToFavorites_ShouldThrowBadRequestException_WhenChallengeUuidIsNull
// Node: addChallengeToFavorites_ShouldThrowBadRequestException_WhenUserUuidIsNotValid
// Node: addChallengeToFavorites_ShouldThrowBadUUIDException_WhenChallengeUuidIsNotValid
// Node: getUserFavorites_WhenUserHasNoFavorites_ReturnsEmptySet
// Node: getUserFavorites_WhenUserExistsWithFavorites_ReturnsFavorites
// Node: getUserFavorites_WhenUserNotFound_ThrowsNotFoundException
// Node: getUserFavorites_WhenInvalidUUID_ThrowsBadUUIDException
// Node: getUserFavorites_WhenRepositoryError_PropagatesError
// Node: deleteChallengeFromFavorites_ShouldThrowNotFoundException_WhenUserNotFound
// Node: deleteChallengeFromFavorites_ShouldThrowBadRequestException_WhenUserUuidIsNull
// Node: deleteChallengeFromFavorites_ShouldThrowBadRequestException_WhenChallengeUuidIsNull
// Node: deleteChallengeFromFavorites_ShouldThrowBadRequestException_WhenUserUuidIsNotValid
// Node: deleteChallengeFromFavorites_ShouldThrowBadRequestException_WhenChallengeUuidIsNotValid
// Node: deleteChallengeFromFavorites_ShouldReturnFalse_WhenFavoriteDoesNotExist
// Node: deleteChallengeFromFavorites_ShouldReturnTrue_WhenFavoriteAlreadyExists
// Node: bodyValue
// Node: exchange
// Node: expectStatus
// Node: isOk
// Node: expectBody
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


// Node: createUser_withNewUser_shouldReturn201Created
// Node: AdminCreateUserRequestDto
// Node: setUsername
// Node: post
// Node: isCreated
// Node: createUser_withExistingUser_shouldReturn409Conflict
package com.itachallenge.user.controller;

import com.itachallenge.user.document.UserDocument;
import com.itachallenge.user.document.enums.Role;
import com.itachallenge.user.exception.BadUUIDException;
import com.itachallenge.user.exception.NotFoundException;
import com.itachallenge.user.exception.UserGlobalExceptionHandler;
import com.itachallenge.user.service.IUserSolutionService;
import com.itachallenge.user.service.UserService;
import org.junit.jupiter.api.*;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.springframework.http.HttpStatus;
import org.springframework.test.web.reactive.server.WebTestClient;
import reactor.core.publisher.Mono;

import java.util.UUID;

import static org.mockito.Mockito.*;

class UserControllerTest {

    @Mock
    private UserService userService;

    @Mock
    private IUserSolutionService userSolutionService;

    @InjectMocks
    private UserController userController;

    private WebTestClient webTestClient;

    private AutoCloseable mocks;

    @BeforeEach
    void setUp() {
        mocks = MockitoAnnotations.openMocks(this);
        webTestClient = WebTestClient.bindToController(userController)
                .controllerAdvice(new UserGlobalExceptionHandler())
                .build();
    }

    @AfterEach
    void tearDown() throws Exception {
        if (mocks != null) {
            mocks.close();
        }
    }

    @Test
    void testEndpoint_ShouldReturnHelloMessage() {
        webTestClient.get()
                .uri("/itachallenge/api/v1/user/test")
                .exchange()
                .expectStatus().isOk()
                .expectBody(String.class).isEqualTo("Hello from ITA Challenge UserController!!!");
    }

    @Test
    void getUser_WhenUserExists_Returns200() {
        String githubUsername = "existingUser";
        UserDocument expectedUser = new UserDocument(UUID.randomUUID(), githubUsername, Role.ADMIN, 0);
        when(userService.getUser(githubUsername)).thenReturn(Mono.just(expectedUser));

        webTestClient.get()
                .uri("/itachallenge/api/v1/user/users/" + githubUsername)
                .exchange()
                .expectStatus().isOk()
                .expectHeader().exists("X-Validation-Status")
                .expectHeader().valueEquals("X-Validation-Status", "Success")
                .expectHeader().valueEquals("X-Github-Username", githubUsername)
                .expectBody(UserDocument.class).isEqualTo(expectedUser);

        verify(userService, times(1)).getUser(githubUsername);
    }

    @Test
    void getUser_WhenUserNotExists_Returns404() {
        String githubUsername = "nonExistentUser";
        when(userService.getUser(githubUsername)).thenReturn(Mono.error(new NotFoundException("User not found")));

        webTestClient.get()
                .uri("/itachallenge/api/v1/user/users/" + githubUsername)
                .exchange()
                .expectStatus().isNotFound()
                .expectBody(String.class).isEqualTo("User not found");

        verify(userService, times(1)).getUser(githubUsername);
    }

    @Test
    void getUser_WhenServiceReturnsError_Returns500() {
        String githubUsername = "username";
        when(userService.getUser(any(String.class))).thenReturn(Mono.error( new RuntimeException()));

        webTestClient.get()
                .uri("/itachallenge/api/v1/user/users/" + githubUsername)
                .exchange()
                .expectStatus().isEqualTo(HttpStatus.INTERNAL_SERVER_ERROR)
                .expectBody(String.class).isEqualTo("Unexpected error happened.");

        verify(userService, times(1)).getUser(githubUsername);
    }

    @Test
    void addToBookmarks_WhenAdded_Returns201() {
        String userId = UUID.randomUUID().toString();
        String challengeId = UUID.randomUUID().toString();
        when(userService.addChallengeToBookmarks(userId, challengeId))
                .thenReturn(Mono.just(true));

        webTestClient.post()
                .uri("/itachallenge/api/v1/user/users/" + userId + "/bookmarks/" + challengeId)
                .exchange()
                .expectStatus().isEqualTo(HttpStatus.CREATED)
                .expectBody(Boolean.class).isEqualTo(true);

        verify(userService, times(1)).addChallengeToBookmarks(userId, challengeId);
    }

    @Test
    void addToBookmarks_WhenAlreadyInBookmarks_Returns200() {
        String userId = UUID.randomUUID().toString();
        String challengeId = UUID.randomUUID().toString();
        when(userService.addChallengeToBookmarks(userId, challengeId))
                .thenReturn(Mono.just(false));

        webTestClient.post()
                .uri("/itachallenge/api/v1/user/users/" + userId + "/bookmarks/" + challengeId)
                .exchange()
                .expectStatus().isOk()
                .expectBody(Boolean.class).isEqualTo(false);

        verify(userService, times(1)).addChallengeToBookmarks(userId, challengeId);
    }

    @Test
    void addToBookmarks_WhenUserNotExists_Returns404() {
        String userId = UUID.randomUUID().toString();
        String challengeId = UUID.randomUUID().toString();
        when(userService.addChallengeToBookmarks(userId, challengeId))
                .thenReturn(Mono.error(new NotFoundException("User not found")));

        webTestClient.post()
                .uri("/itachallenge/api/v1/user/users/" + userId + "/bookmarks/" + challengeId)
                .exchange()
                .expectStatus().isEqualTo(HttpStatus.NOT_FOUND)
                .expectBody(String.class).isEqualTo("User not found");

        verify(userService, times(1)).addChallengeToBookmarks(userId, challengeId);
    }

    @Test
    void addToBookmarks_WhenBadFormattedId_Returns400() {
        String userId = "invalidUuid";
        String challengeId = "invalidUUid";
        when(userService.addChallengeToBookmarks(userId, challengeId))
                .thenReturn(Mono.error(new BadUUIDException("Error message")));

        webTestClient.post()
                .uri("/itachallenge/api/v1/user/users/" + userId + "/bookmarks/" + challengeId)
                .exchange()
                .expectStatus().isEqualTo(HttpStatus.BAD_REQUEST)
                .expectBody(String.class).isEqualTo("The provided IDs are not valid.");

        verify(userService, times(1)).addChallengeToBookmarks(userId, challengeId);
    }

    @Test
    void addToBookmarks_WhenUnexpectedError_Returns500() {
        String userId = UUID.randomUUID().toString();
        String challengeId = UUID.randomUUID().toString();
        when(userService.addChallengeToBookmarks(userId, challengeId))
                .thenReturn(Mono.error(new Exception()));

        webTestClient.post()
                .uri("/itachallenge/api/v1/user/users/" + userId + "/bookmarks/" + challengeId)
                .exchange()
                .expectStatus().isEqualTo(HttpStatus.INTERNAL_SERVER_ERROR)
                .expectBody(String.class).isEqualTo("Unexpected error happened.");

        verify(userService, times(1)).addChallengeToBookmarks(userId, challengeId);
    }

    @Test
    void deleteFromBookmarks_WhenDeleted_Returns200() {
        String userId = UUID.randomUUID().toString();
        String challengeId = UUID.randomUUID().toString();
        when(userService.deleteChallengeFromBookmarks(userId, challengeId))
                .thenReturn(Mono.just(true));

        webTestClient.delete()
                .uri("/itachallenge/api/v1/user/users/" + userId + "/bookmarks/" + challengeId)
                .exchange()
                .expectStatus().isEqualTo(HttpStatus.OK)
                .expectBody(Boolean.class).isEqualTo(true);

        verify(userService, times(1)).deleteChallengeFromBookmarks(userId, challengeId);
    }

    @Test
    void deleteFromBookmarks_WhenNotInBookmarks_Returns200() {
        String userId = UUID.randomUUID().toString();
        String challengeId = UUID.randomUUID().toString();
        when(userService.deleteChallengeFromBookmarks(userId, challengeId))
                .thenReturn(Mono.just(false));

        webTestClient.delete()
                .uri("/itachallenge/api/v1/user/users/" + userId + "/bookmarks/" + challengeId)
                .exchange()
                .expectStatus().isOk()
                .expectBody(Boolean.class).isEqualTo(false);

        verify(userService, times(1)).deleteChallengeFromBookmarks(userId, challengeId);
    }

    @Test
    void deleteFromBookmarks_WhenUserNotExists_Returns404() {
        String userId = UUID.randomUUID().toString();
        String challengeId = UUID.randomUUID().toString();
        when(userService.deleteChallengeFromBookmarks(userId, challengeId))
                .thenReturn(Mono.error(new NotFoundException("User not found")));

        webTestClient.delete()
                .uri("/itachallenge/api/v1/user/users/" + userId + "/bookmarks/" + challengeId)
                .exchange()
                .expectStatus().isEqualTo(HttpStatus.NOT_FOUND)
                .expectBody(String.class).isEqualTo("User not found");

        verify(userService, times(1)).deleteChallengeFromBookmarks(userId, challengeId);
    }

    @Test
    void deleteFromBookmarks_WhenBadFormattedId_Returns404() {
        String userId = "invalidUuid";
        String challengeId = "invalidUUid";
        when(userService.deleteChallengeFromBookmarks(userId, challengeId))
                .thenReturn(Mono.error(new BadUUIDException("Error message")));

        webTestClient.delete()
                .uri("/itachallenge/api/v1/user/users/" + userId + "/bookmarks/" + challengeId)
                .exchange()
                .expectStatus().isEqualTo(HttpStatus.BAD_REQUEST)
                .expectBody(String.class).isEqualTo("The provided IDs are not valid.");

        verify(userService, times(1)).deleteChallengeFromBookmarks(userId, challengeId);
    }

    @Test
    void deleteFromBookmarks_WhenUnexpectedError_Returns500() {
        String userId = UUID.randomUUID().toString();
        String challengeId = UUID.randomUUID().toString();
        when(userService.deleteChallengeFromBookmarks(userId, challengeId))
                .thenReturn(Mono.error(new Exception()));

        webTestClient.delete()
                .uri("/itachallenge/api/v1/user/users/" + userId + "/bookmarks/" + challengeId)
                .exchange()
                .expectStatus().isEqualTo(HttpStatus.INTERNAL_SERVER_ERROR)
                .expectBody(String.class).isEqualTo("Unexpected error happened.");

        verify(userService, times(1)).deleteChallengeFromBookmarks(userId, challengeId);
    }

}

// Node: testEndpoint_ShouldReturnHelloMessage
// Node: getUser_WhenUserExists_Returns200
// Node: expectHeader
// Node: valueEquals
// Node: getUser_WhenUserNotExists_Returns404
// Node: isNotFound
// Node: getUser_WhenServiceReturnsError_Returns500
// Node: addToBookmarks_WhenAdded_Returns201
// Node: addToBookmarks_WhenAlreadyInBookmarks_Returns200
// Node: addToBookmarks_WhenUserNotExists_Returns404
// Node: addToBookmarks_WhenBadFormattedId_Returns400
// Node: addToBookmarks_WhenUnexpectedError_Returns500
// Node: deleteFromBookmarks_WhenDeleted_Returns200
// Node: deleteFromBookmarks_WhenNotInBookmarks_Returns200
// Node: deleteFromBookmarks_WhenUserNotExists_Returns404
// Node: deleteFromBookmarks_WhenBadFormattedId_Returns404
// Node: deleteFromBookmarks_WhenUnexpectedError_Returns500
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

// Node: getUserBookmarks_NewPath_Success
// Node: expectBodyList
// Node: getUserBookmarks_returnsBookmarks
// Node: getUserBookmarks_returns404IfUserNotFound
// Node: getUserBookmarks_returns400IfInvalidUUID
// Node: isBadRequest
// Node: getUserBookmarks_returns500IfUnexpectedError
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


// Node: addToFavorites_WhenAdded_Returns201
// Node: addToFavorites_WhenAlreadyInFavorites_Returns200
// Node: addToFavorites_WhenUserNotExists_Returns404
// Node: addToFavorites_WhenBadFormattedId_Returns400
// Node: addToFavorites_WhenUnexpectedError_Returns500
// Node: getUserFavorites_returnsFavorites
// Node: getUserFavorites_returns404IfUserNotFound
// Node: getUserFavorites_returns400IfInvalidUUID
// Node: deleteFromFavorites_WhenDeleted_Returns200
// Node: deleteFromFavorites_WhenNotInFavorites_Returns200
// Node: deleteFromFavorites_WhenUserNotExists_Returns404
// Node: deleteFromFavorites_WhenBadFormattedId_Returns404
// Node: deleteFromFavorites_WhenUnexpectedError_Returns500
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


// Node: getUserFavorites_WithExistingFavorites_ReturnsSetOfChallengeIds
// Node: addFavorite
// Node: accept
// Node: containsExactlyInAnyOrder
// Node: getUserFavorites_WithNoFavorites_ReturnsEmptySet
// Node: getUserFavorites_WithMultipleFavoritesFromDifferentUsers_ReturnsOnlyUserFavorites
// Node: getUserFavorites_WithInvalidUUID_Returns400
// Node: jsonPath
// Node: getUserFavorites_WhenUserDoesntExist_Returns404
// Node: returnResult
// Node: getResponseBody
// Node: setSolutionText
package com.itachallenge.user.service;

import com.itachallenge.user.document.UserDocument;
import com.itachallenge.user.document.enums.Role;
import com.itachallenge.user.exception.BadUUIDException;
import com.itachallenge.user.exception.NotFoundException;
import com.itachallenge.user.repository.UserRepository;
import com.itachallenge.userinteraction.document.bookmark.BookmarkDocument;
import com.itachallenge.userinteraction.repository.bookmark.BookmarkRepository;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;

import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.mockito.Mockito.*;


class UserServiceImplTest {

    @Mock
    private UserRepository userRepository;

    @Mock
    private BookmarkRepository bookmarkRepository;

    @InjectMocks
    private UserServiceImpl userService;

    private AutoCloseable mocks;

    @BeforeEach
    void setUp() {
        mocks = MockitoAnnotations.openMocks(this);
    }

    @AfterEach
    void tearDown() throws Exception {
        if (mocks != null) {
            mocks.close();
        }
    }

    @Test
    void getUser_ShouldReturnUser_WhenUserExists() {
        String username = "existingUser";
        UserDocument existingUser = new UserDocument(UUID.randomUUID(), username, Role.ADMIN, 0);
        when(userRepository.findByUsername(username)).thenReturn(Mono.just(existingUser));

        StepVerifier.create(userService.getUser(username))
                .expectNext(existingUser)
                .verifyComplete();

        verify(userRepository, times(1)).findByUsername(username);
    }

    @Test
    void getUser_ShouldReturnNotFoundException_WhenUserDoesNotExist() {
        String username = "nonExistentUser";
        when(userRepository.findByUsername(username)).thenReturn(Mono.empty());

        StepVerifier.create(userService.getUser(username))
                .expectErrorSatisfies(error -> {
                    assertInstanceOf(NotFoundException.class, error);
                    assertEquals("User not found", error.getMessage());
                })
                .verify();

        verify(userRepository, times(1)).findByUsername(username);
    }

    @Test
    void addChallengeToBookmarks_ShouldReturnTrue_WhenBookmarksIsNull() {
        UUID userId = UUID.randomUUID();
        UUID challengeId = UUID.randomUUID();
        UserDocument user = new UserDocument(userId, "testUser", null, 0);

        when(userRepository.findById(userId)).thenReturn(Mono.just(user));
        when(bookmarkRepository.existsByUserIdAndChallengeId(userId, challengeId))
                .thenReturn(Mono.just(false));
        when(bookmarkRepository.save(any(BookmarkDocument.class)))
                .thenReturn(Mono.just(new BookmarkDocument()));

        StepVerifier.create(userService.addChallengeToBookmarks(userId.toString(), challengeId.toString()))
                .expectNext(true)
                .verifyComplete();

        verify(userRepository, times(1)).findById(userId);
        verify(bookmarkRepository, times(1)).existsByUserIdAndChallengeId(userId, challengeId);
        verify(bookmarkRepository, times(1)).save(any(BookmarkDocument.class));
        verify(userRepository, never()).save(any());
    }

    @Test
    void addChallengeToBookmarks_ShouldReturnTrue_WhenBookmarksIsEmpty() {
        UUID challengeId = UUID.randomUUID();
        UUID userId = UUID.randomUUID();
        UserDocument user = new UserDocument(userId, "testUser", null, 0);

        when(userRepository.findById(userId)).thenReturn(Mono.just(user));
        when(bookmarkRepository.existsByUserIdAndChallengeId(userId, challengeId))
                .thenReturn(Mono.just(false));
        when(bookmarkRepository.save(any(BookmarkDocument.class)))
                .thenReturn(Mono.just(new BookmarkDocument()));

        StepVerifier.create(userService.addChallengeToBookmarks(userId.toString(), challengeId.toString()))
                .expectNext(true)
                .verifyComplete();

        verify(userRepository, times(1)).findById(userId);
        verify(bookmarkRepository, times(1)).existsByUserIdAndChallengeId(userId, challengeId);
        verify(bookmarkRepository, times(1)).save(any(BookmarkDocument.class));
    }

    @Test
    void addChallengeToBookmarks_ShouldReturnTrue_WhenBookmarksHasValues() {
        UUID challengeId = UUID.randomUUID();
        UUID userId = UUID.randomUUID();
        UserDocument user = new UserDocument(userId, "testUser", null, 0);

        when(userRepository.findById(userId)).thenReturn(Mono.just(user));
        when(bookmarkRepository.existsByUserIdAndChallengeId(userId, challengeId))
                .thenReturn(Mono.just(false));
        when(bookmarkRepository.save(any(BookmarkDocument.class)))
                .thenReturn(Mono.just(new BookmarkDocument()));

        StepVerifier.create(userService.addChallengeToBookmarks(userId.toString(), challengeId.toString()))
                .expectNext(true)
                .verifyComplete();

        verify(userRepository, times(1)).findById(userId);
        verify(bookmarkRepository, times(1)).existsByUserIdAndChallengeId(userId, challengeId);
        verify(bookmarkRepository, times(1)).save(any());
    }

    @Test
    void addChallengeToBookmarks_ShouldReturnFalse_WhenBookmarksAlreadyContainsChallenge() {
        UUID challengeId = UUID.randomUUID();
        UUID userId = UUID.randomUUID();
        UserDocument user = new UserDocument(userId, "testUser", null, 0);

        when(userRepository.findById(userId)).thenReturn(Mono.just(user));
        when(bookmarkRepository.existsByUserIdAndChallengeId(userId, challengeId))
                .thenReturn(Mono.just(true));

        StepVerifier.create(userService.addChallengeToBookmarks(userId.toString(), challengeId.toString()))
                .expectNext(false)
                .verifyComplete();

        verify(userRepository, times(1)).findById(userId);
        verify(bookmarkRepository, times(1)).existsByUserIdAndChallengeId(userId, challengeId);
        verify(bookmarkRepository, never()).save(any());
    }

    @Test
    void addChallengeToBookmarks_ShouldThrowBadRequestException_WhenChallengeUuidIsNull() {
        StepVerifier.create(userService.addChallengeToBookmarks(UUID.randomUUID().toString(), null))
                .expectErrorSatisfies(throwable -> {
                    assertInstanceOf(BadUUIDException.class, throwable);
                    assertEquals("Invalid ID format", throwable.getMessage());
                })
                .verify();

        verify(userRepository, times(0)).findById(any(UUID.class));
        verify(userRepository, times(0)).save(any());
    }

    @Test
    void addChallengeToBookmarks_ShouldThrowBadRequestException_WhenUserUuidIsNotValid() {
        StepVerifier.create(userService.addChallengeToBookmarks("invalidUuid", UUID.randomUUID().toString()))
                .expectErrorSatisfies(throwable -> {
                    assertInstanceOf(BadUUIDException.class, throwable);
                    assertEquals("Invalid ID format", throwable.getMessage());
                })
                .verify();

        verify(userRepository, times(0)).findById(any(UUID.class));
        verify(userRepository, times(0)).save(any());
    }

    @Test
    void addChallengeToBookmarks_ShouldThrowBadRequestException_WhenChallengeUuidIsNotValid() {
        StepVerifier.create(userService.addChallengeToBookmarks(UUID.randomUUID().toString(), "invalidUuid"))
                .expectErrorSatisfies(throwable -> {
                    assertInstanceOf(BadUUIDException.class, throwable);
                    assertEquals("Invalid ID format", throwable.getMessage());
                })
                .verify();

        verify(userRepository, times(0)).findById(any(UUID.class));
        verify(userRepository, times(0)).save(any());
    }


    @Test
    void deleteChallengeFromBookmarks_ShouldReturnFalse_WhenBookmarksIsNull() {
        UUID challengeId = UUID.randomUUID();
        UUID userId = UUID.randomUUID();
        UserDocument user = new UserDocument(userId, "testUser", null, 0);

        when(userRepository.findById(userId)).thenReturn(Mono.just(user));
        when(bookmarkRepository.findByUserIdAndChallengeId(any(UUID.class), any(UUID.class)))
                .thenReturn(Mono.empty());

        StepVerifier.create(userService.deleteChallengeFromBookmarks(userId.toString(), challengeId.toString()))
                .expectNext(false)
                .verifyComplete();

        verify(userRepository, times(1)).findById(userId);
        verify(bookmarkRepository).findByUserIdAndChallengeId(any(UUID.class), any(UUID.class));
        verify(bookmarkRepository, never()).delete(any());
    }

    @Test
    void deleteChallengeFromBookmarks_ShouldReturnFalse_WhenBookmarksIsEmpty() {
        UUID challengeId = UUID.randomUUID();
        UUID userId = UUID.randomUUID();
        UserDocument user = new UserDocument(userId, "testUser", null, 0);

        when(userRepository.findById(userId)).thenReturn(Mono.just(user));
        when(bookmarkRepository.findByUserIdAndChallengeId(any(UUID.class), any(UUID.class)))
                .thenReturn(Mono.empty());

        StepVerifier.create(userService.deleteChallengeFromBookmarks(userId.toString(), challengeId.toString()))
                .expectNext(false)
                .verifyComplete();

        verify(userRepository, times(1)).findById(userId);
        verify(bookmarkRepository).findByUserIdAndChallengeId(any(UUID.class), any(UUID.class));
        verify(bookmarkRepository, never()).delete(any());
    }

    @Test
    void deleteChallengeFromBookmarks_ShouldReturnFalse_WhenChallengeNotInBookmarks() {
        UUID challengeId = UUID.randomUUID();
        UUID userId = UUID.randomUUID();
        UserDocument user = new UserDocument(userId, "testUser", null, 0);

        when(userRepository.findById(userId)).thenReturn(Mono.just(user));
        when(bookmarkRepository.findByUserIdAndChallengeId(any(UUID.class), any(UUID.class)))
                .thenReturn(Mono.empty());

        StepVerifier.create(userService.deleteChallengeFromBookmarks(userId.toString(), challengeId.toString()))
                .expectNext(false)
                .verifyComplete();

        verify(userRepository, times(1)).findById(userId);
        verify(bookmarkRepository).findByUserIdAndChallengeId(any(UUID.class), any(UUID.class));
        verify(bookmarkRepository, never()).delete(any());
    }

    @Test
    void deleteChallengeFromBookmarks_ShouldReturnTrue_WhenBookmarksAlreadyContainsChallenge() {
        UUID challengeId = UUID.randomUUID();
        UUID userId = UUID.randomUUID();
        UserDocument user = new UserDocument(userId, "testUser", null, 0);
        BookmarkDocument bookmark = BookmarkDocument.builder()
                .uuid(UUID.randomUUID())
                .userId(userId)
                .challengeId(challengeId)
                .build();

        when(userRepository.findById(userId)).thenReturn(Mono.just(user));
        when(bookmarkRepository.findByUserIdAndChallengeId(userId, challengeId))
                .thenReturn(Mono.just(bookmark));
        when(bookmarkRepository.delete(any(BookmarkDocument.class))).thenReturn(Mono.empty());

        StepVerifier.create(userService.deleteChallengeFromBookmarks(userId.toString(), challengeId.toString()))
                .expectNext(true)
                .verifyComplete();

        verify(userRepository).findById(userId);
        verify(bookmarkRepository).findByUserIdAndChallengeId(userId, challengeId);
        verify(bookmarkRepository).delete(bookmark);
    }

    @Test
    void deleteChallengeFromBookmarks_ShouldThrowNotFoundException_WhenUserNotFound() {

        when(userRepository.findById(any(UUID.class))).thenReturn(Mono.empty());

        StepVerifier.create(userService.deleteChallengeFromBookmarks(UUID.randomUUID().toString(), UUID.randomUUID().toString()))
                .expectErrorSatisfies(throwable -> {
                    assertInstanceOf(NotFoundException.class, throwable);
                    assertEquals("User not found", throwable.getMessage());
                })
                .verify();

        verify(userRepository, times(1)).findById(any(UUID.class));
        verify(userRepository, times(0)).save(any());
    }

    @Test
    void deleteChallengeFromBookmarks_ShouldThrowBadRequestException_WhenUserUuidIsNull() {
        StepVerifier.create(userService.deleteChallengeFromBookmarks(null, UUID.randomUUID().toString()))
                .expectErrorSatisfies(throwable -> {
                    assertInstanceOf(BadUUIDException.class, throwable);
                    assertEquals("Invalid ID format", throwable.getMessage());
                })
                .verify();

        verify(userRepository, times(0)).findById(any(UUID.class));
        verify(userRepository, times(0)).save(any());
    }

    @Test
    void deleteChallengeFromBookmarks_ShouldThrowBadRequestException_WhenChallengeUuidIsNull() {
        StepVerifier.create(userService.deleteChallengeFromBookmarks(UUID.randomUUID().toString(), null))
                .expectErrorSatisfies(throwable -> {
                    assertInstanceOf(BadUUIDException.class, throwable);
                    assertEquals("Invalid ID format", throwable.getMessage());
                })
                .verify();

        verify(userRepository, times(0)).findById(any(UUID.class));
        verify(userRepository, times(0)).save(any());
    }

    @Test
    void deleteChallengeFromBookmarks_ShouldThrowBadRequestException_WhenUserUuidIsNotValid() {
        StepVerifier.create(userService.deleteChallengeFromBookmarks("invalidUuid", UUID.randomUUID().toString()))
                .expectErrorSatisfies(throwable -> {
                    assertInstanceOf(BadUUIDException.class, throwable);
                    assertEquals("Invalid ID format", throwable.getMessage());
                })
                .verify();

        verify(userRepository, times(0)).findById(any(UUID.class));
        verify(userRepository, times(0)).save(any());
    }

    @Test
    void deleteChallengeFromBookmarks_ShouldThrowBadRequestException_WhenChallengeUuidIsNotValid() {
        StepVerifier.create(userService.deleteChallengeFromBookmarks(UUID.randomUUID().toString(), "invalidUuid"))
                .expectErrorSatisfies(throwable -> {
                    assertInstanceOf(BadUUIDException.class, throwable);
                    assertEquals("Invalid ID format", throwable.getMessage());
                })
                .verify();

        verify(userRepository, times(0)).findById(any(UUID.class));
        verify(userRepository, times(0)).save(any());
    }

    @Test
    @DisplayName("getUserById returns the user when the user exists")
    void getUserById_ShouldReturnUser_WhenUserExists() {
        String username = "existingUser";
        UUID userId=UUID.randomUUID();
        UserDocument existingUser = new UserDocument(userId, username, Role.ADMIN, 0);
        when(userRepository.findById(userId)).thenReturn(Mono.just(existingUser));

        StepVerifier.create(userService.getUserById(userId.toString()))
                .expectNext(existingUser)
                .verifyComplete();

        verify(userRepository, times(1)).findById(userId);
    }

    @Test
    @DisplayName("getUserById throws NotFoundException when the user does not exist")
    void getUserById_ShouldReturnNotFoundException_WhenUserDoesNotExist() {
        UUID userId=UUID.randomUUID();
        when(userRepository.findById(userId)).thenReturn(Mono.empty());

        StepVerifier.create(userService.getUserById(userId.toString()))
                .expectErrorSatisfies(error -> {
                    assertInstanceOf(NotFoundException.class, error);
                    assertEquals("User not found", error.getMessage());
                })
                .verify();
        verify(userRepository, times(1)).findById(userId);
    }
}


// Node: getUser_ShouldReturnUser_WhenUserExists
// Node: getUser_ShouldReturnNotFoundException_WhenUserDoesNotExist
// Node: addChallengeToBookmarks_ShouldReturnTrue_WhenBookmarksIsNull
// Node: addChallengeToBookmarks_ShouldReturnTrue_WhenBookmarksIsEmpty
// Node: addChallengeToBookmarks_ShouldReturnTrue_WhenBookmarksHasValues
// Node: addChallengeToBookmarks_ShouldReturnFalse_WhenBookmarksAlreadyContainsChallenge
// Node: addChallengeToBookmarks_ShouldThrowBadRequestException_WhenChallengeUuidIsNull
// Node: addChallengeToBookmarks_ShouldThrowBadRequestException_WhenUserUuidIsNotValid
// Node: addChallengeToBookmarks_ShouldThrowBadRequestException_WhenChallengeUuidIsNotValid
// Node: deleteChallengeFromBookmarks_ShouldReturnFalse_WhenBookmarksIsNull
// Node: deleteChallengeFromBookmarks_ShouldReturnFalse_WhenBookmarksIsEmpty
// Node: deleteChallengeFromBookmarks_ShouldReturnFalse_WhenChallengeNotInBookmarks
// Node: deleteChallengeFromBookmarks_ShouldReturnTrue_WhenBookmarksAlreadyContainsChallenge
// Node: deleteChallengeFromBookmarks_ShouldThrowNotFoundException_WhenUserNotFound
// Node: deleteChallengeFromBookmarks_ShouldThrowBadRequestException_WhenUserUuidIsNull
// Node: deleteChallengeFromBookmarks_ShouldThrowBadRequestException_WhenChallengeUuidIsNull
// Node: deleteChallengeFromBookmarks_ShouldThrowBadRequestException_WhenUserUuidIsNotValid
// Node: deleteChallengeFromBookmarks_ShouldThrowBadRequestException_WhenChallengeUuidIsNotValid
// Node: getUserById_ShouldReturnUser_WhenUserExists
// Node: getUserById_ShouldReturnNotFoundException_WhenUserDoesNotExist
// Node: anyString
package com.itachallenge.user.service;

import com.itachallenge.githubcore.document.enums.GithubUserStatus;
import com.itachallenge.githubcore.exception.GithubUnavailableException;
import com.itachallenge.githubcore.service.GithubApiService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;

class ExternalGithubServiceImplTest {

    private GithubApiService githubApiService;
    private ExternalGithubServiceImpl externalGithubService;

    @BeforeEach
    void setUp() {
        githubApiService = Mockito.mock(GithubApiService.class);
        externalGithubService = new ExternalGithubServiceImpl(githubApiService);
    }

    @Test
    @DisplayName("Should return true when GitHub user exists")
    void testUserExistsReturnsTrue() {
        when(githubApiService.userExists(anyString()))
                .thenReturn(Mono.just(GithubUserStatus.FOUND));

        StepVerifier.create(externalGithubService.userExists("someUser"))
                .expectNext(true)
                .verifyComplete();
    }

    @Test
    @DisplayName("Should return false when GitHub user is NOT_FOUND")
    void testUserExistsReturnsFalse() {
        when(githubApiService.userExists(anyString()))
                .thenReturn(Mono.just(GithubUserStatus.NOT_FOUND));

        StepVerifier.create(externalGithubService.userExists("ghostUser"))
                .expectNext(false)
                .verifyComplete();
    }

    @Test
    @DisplayName("Should wrap API errors in GithubUnavailableException, preserving the cause")
    void testUserExistsPropagatesError() {
        RuntimeException originalLowLevelError = new RuntimeException("Original low-level API error.");

        when(githubApiService.userExists(anyString()))
                .thenReturn(Mono.error(originalLowLevelError));

        StepVerifier.create(externalGithubService.userExists("anyUser"))
                .expectErrorMatches(throwable ->
                        throwable instanceof GithubUnavailableException &&
                                throwable.getCause() == originalLowLevelError &&
                                throwable.getMessage().equals("Error connecting to GitHub API."))
                .verify();
    }
}


// Node: testUserExistsPropagatesError
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

// Node: createUser_whenUserDoesNotExistInDB_shouldCreateAndReturnUser
// Node: createUser_whenUserDoesNotExistInDBAndIsNotAGithubUser_shouldThrowException
// Node: createUser_whenUserAlreadyExists_shouldThrowException
// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/test/java/com/itachallenge/user/service/AdminCreateUserServiceTest.java:AdminCreateUserServiceTest.createUser_whenGithubApiTimeout_shouldThrowGithubUnavailableException
// Node: createUser_whenGithubApiTimeout_shouldThrowGithubUnavailableException
// Node: delay
// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/test/java/com/itachallenge/user/service/AdminCreateUserServiceTest.java:AdminCreateUserServiceTest.createUser_whenGithubApiFailsImmediately_shouldThrowGithubUnavailableException
// Node: createUser_whenGithubApiFailsImmediately_shouldThrowGithubUnavailableException
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

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/test/java/com/itachallenge/user/dto/UserSolutionRequestDtoTest.java:UserSolutionRequestDtoTest.<init>
// Node: getAllSubmissionsByUser
package com.itachallenge.challenge.exception;

public class JwtException extends RuntimeException {
    public JwtException(String message) {
        super(message);
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/exception/JwtException.java:JwtException.<init>
package com.itachallenge.challenge.exception;

public class UserNotFoundException extends RuntimeException {

    public UserNotFoundException(String message) {
        super(message);
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/exception/UserNotFoundException.java:UserNotFoundException.<init>
// Node: UserNotFoundException
// Node: removeFavorite
// Node: removeChallengeFromFavorites
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



// Node: getResourcesByChallengeId
// Node: updateChallenge
// Node: removeChallengeFromBookmarks
package com.itachallenge.challenge.service;

import reactor.core.publisher.Mono;

public interface IUserService {
    Mono<Boolean> addChallengeToFavorites(String userId, String challengeId);

    Mono<Boolean> addChallengeToBookmarks(String userId, String challengeId);
    Mono<Boolean> removeChallengeFromFavorites(String userId, String challengeId);

    Mono<Boolean> removeChallengeFromBookmarks(String userId, String challengeId);

}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/service/IUserService.java:IUserService.<init>
// Node: setIdChallenge
package com.itachallenge.challenge.service;

import com.itachallenge.challenge.dto.FavoriteDto;
import reactor.core.publisher.Mono;

public interface IFavoriteService {

    Mono<FavoriteDto> addChallengeToFavorites(String challengeId, String userId);

    Mono<FavoriteDto> removeChallengeFromFavorites(String challengeId, String userId);
}

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/service/IFavoriteService.java:IFavoriteService.<init>
package com.itachallenge.challenge.service;

import com.itachallenge.jwtcore.service.IJwtService;
import io.jsonwebtoken.Claims;
import org.springframework.stereotype.Service;

@Service
public class ChallengeJwtFacade implements IChallengeJwtFacade {

    private final IJwtService jwtService;

    public ChallengeJwtFacade(IJwtService jwtService) {
        this.jwtService = jwtService;
    }

    @Override
    public Claims extractAllClaims(String token) {
        return jwtService.extractAllClaims(token);
    }

    @Override
    public String getUserUuIdFromAuthenticationHeader(String authHeader) {
        return jwtService.getUserUuIdFromAuthenticationHeader(authHeader);
    }
}


// Node: SolutionDto
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


// Node: getAllSubmissionsByUser_shouldThrow_whenUserIdIsNull
// Node: getAllSubmissionsByUser_shouldThrow_whenUserIdIsEmpty
// Node: getAllSubmissionsByUser_shouldThrow_whenUserIdIsInvalidUuid
// Node: MethodSource
// Node: ChallengeCreateDto
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


// Node: getAllChallenges_ValidPageParameters_ChallengesReturned
// Node: getAllChallenges_NullPageParameters_ChallengesReturned
// Node: getSolutions_ValidIds_SolutionsReturned
// Node: getChallengesByFilter_ValidParams_ChallengesReturned
// Node: queryParam
// Node: getRelatedChallenges_ValidId_Returns200_RelatedChallengesReturned
// Node: consumeWith
// Node: getRelatedChallenges_InvalidUUID_Returns400
// Node: getRelatedChallenges_NoContent_Returns204
// Node: isNoContent
// Node: AddSolution_validIdChallenge_validIdLanguage
// Node: addSolution_NullSolutionText_ThrowsBadRequestException
// Node: getDefault
// Node: addSolution_EmptySolutionText_ThrowsBadRequestException
// Node: addSolution_NullChallengeId_ThrowsBadRequestException
// Node: addSolution_NullLanguageId_ThrowsBadRequestException
// Node: addSolution_NullSolutionDto_ThrowsBadRequestException
// Node: addChallenge_test_validRequest
// Node: addChallenge_test_emptyField_statusBadRequest
// Node: addChallenge_test_invalidLanguage_statusBadRequest
// Node: thenThrow
// Node: addChallenge_test_invalidLevel_statusBadRequest
// Node: getVersionTest
// Node: addChallengeToBookmarks_Success_Returns200
// Node: addChallengeToBookmarks_InternalServerError_Returns500
// Node: addChallengeToBookmarks_InvalidHeader_Returns400
// Node: addChallengeToBookmarks_MissingHeader_Returns400
// Node: getChallengesByFilter_shouldReturnOkResponse
// Node: updateChallengeValidRequest_AuthorizedUser_Returns200
// Node: updateChallenge_MissingAuthHeader_Returns400
// Node: updateChallengeEmptyField_returnsBadRequest_test
// Node: updateChallengeInvalidEnumValue_returnsBadRequest_test
// Node: removeChallengeFromBookmarks_Success_Returns200
// Node: removeChallengeFromBookmarks_InternalServerError_Returns500
// Node: removeChallengeFromBookmarks_InvalidHeader_Returns400
// Node: removeChallengeFromBookmarks_MissingHeader_Returns400
// Node: addChallenge_emptyTags_statusBadRequest
// Node: deleteChallenge_shouldReturn200Ok
package com.itachallenge.challenge.controller;

import com.itachallenge.challenge.dto.FavoriteDto;
import com.itachallenge.common.exception.BadRequestException;
import com.itachallenge.challenge.exception.ChallengeNotFoundException;
import com.itachallenge.challenge.exception.JwtException;
import com.itachallenge.challenge.exception.InternalServerErrorException;
import com.itachallenge.challenge.service.IFavoriteService;
import com.itachallenge.challenge.service.IChallengeJwtFacade;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.ResponseEntity;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

import static org.mockito.Mockito.*;

public class FavoriteControllerTest {

    private IFavoriteService favoriteService;
    private IChallengeJwtFacade challengeJwtFacade;
    private FavoriteController favoriteController;

    @BeforeEach
    void setUp() {
        favoriteService = mock(IFavoriteService.class);
        challengeJwtFacade = mock(IChallengeJwtFacade.class);
        favoriteController = new FavoriteController(favoriteService, challengeJwtFacade);
    }

    @Test
    void addFavorite_success_200() {
        String challengeId = "123e4567-e89b-12d3-a456-426614174000";
        String userId = "321e4567-e89b-12d3-a456-426614174000";
        String authHeader = "Bearer token";
        FavoriteDto dto = new FavoriteDto(true, 1);

        when(challengeJwtFacade.getUserUuIdFromAuthenticationHeader(authHeader)).thenReturn(userId);
        when(favoriteService.addChallengeToFavorites(challengeId, userId)).thenReturn(Mono.just(dto));

        Mono<ResponseEntity<FavoriteDto>> result = favoriteController.addFavorite(challengeId, authHeader);

        StepVerifier.create(result)
                .expectNextMatches(response -> response.getStatusCode().is2xxSuccessful() &&
                        response.getBody().isFavorite() && response.getBody().getTimesFavorited() == 1)
                .verifyComplete();
    }

    @Test
    void addFavorite_missingAuthHeader_400() {
        String challengeId = "123e4567-e89b-12d3-a456-426614174000";
        String authHeader = null;
        when(challengeJwtFacade.getUserUuIdFromAuthenticationHeader(authHeader)).thenThrow(new JwtException("Missing header"));

        Mono<ResponseEntity<FavoriteDto>> result = favoriteController.addFavorite(challengeId, authHeader);

        StepVerifier.create(result)
                .expectError(BadRequestException.class)
                .verify();
    }

    @Test
    void addFavorite_invalidAuthHeader_400() {
        String challengeId = "123e4567-e89b-12d3-a456-426614174000";
        String authHeader = "invalid";
        when(challengeJwtFacade.getUserUuIdFromAuthenticationHeader(authHeader)).thenThrow(new JwtException("Invalid header"));

        Mono<ResponseEntity<FavoriteDto>> result = favoriteController.addFavorite(challengeId, authHeader);

        StepVerifier.create(result)
                .expectError(BadRequestException.class)
                .verify();
    }

    @Test
    void addFavorite_challengeNotFound_404() {
        String challengeId = "not-found-id";
        String userId = "321e4567-e89b-12d3-a456-426614174000";
        String authHeader = "Bearer token";

        when(challengeJwtFacade.getUserUuIdFromAuthenticationHeader(authHeader)).thenReturn(userId);
        when(favoriteService.addChallengeToFavorites(challengeId, userId))
                .thenReturn(Mono.error(new ChallengeNotFoundException("Challenge not found")));

        Mono<ResponseEntity<FavoriteDto>> result = favoriteController.addFavorite(challengeId, authHeader);

        StepVerifier.create(result)
                .expectError(ChallengeNotFoundException.class)
                .verify();
    }

    @Test
    void addFavorite_internalServerError_500() {
        String challengeId = "123e4567-e89b-12d3-a456-426614174000";
        String userId = "321e4567-e89b-12d3-a456-426614174000";
        String authHeader = "Bearer token";

        when(challengeJwtFacade.getUserUuIdFromAuthenticationHeader(authHeader)).thenReturn(userId);
        when(favoriteService.addChallengeToFavorites(challengeId, userId))
                .thenReturn(Mono.error(new InternalServerErrorException("Internal error")));

        Mono<ResponseEntity<FavoriteDto>> result = favoriteController.addFavorite(challengeId, authHeader);

        StepVerifier.create(result)
                .expectError(InternalServerErrorException.class)
                .verify();
    }

    @Test
    void removeFavorite_success_200() {
        String challengeId = "123e4567-e89b-12d3-a456-426614174000";
        String userId = "321e4567-e89b-12d3-a456-426614174000";
        String authHeader = "Bearer token";
        FavoriteDto dto = new FavoriteDto(false, 0);

        when(challengeJwtFacade.getUserUuIdFromAuthenticationHeader(authHeader)).thenReturn(userId);
        when(favoriteService.removeChallengeFromFavorites(challengeId, userId)).thenReturn(Mono.just(dto));

        Mono<ResponseEntity<FavoriteDto>> result = favoriteController.removeFavorite(challengeId, authHeader);

        StepVerifier.create(result)
                .expectNextMatches(response -> response.getStatusCode().is2xxSuccessful() &&
                        !response.getBody().isFavorite() && response.getBody().getTimesFavorited() == 0)
                .verifyComplete();
    }

    @Test
    void removeFavorite_missingAuthHeader_400() {
        String challengeId = "123e4567-e89b-12d3-a456-426614174000";
        String authHeader = null;
        when(challengeJwtFacade.getUserUuIdFromAuthenticationHeader(authHeader)).thenThrow(new JwtException("Missing header"));

        Mono<ResponseEntity<FavoriteDto>> result = favoriteController.removeFavorite(challengeId, authHeader);

        StepVerifier.create(result)
                .expectError(BadRequestException.class)
                .verify();
    }

    @Test
    void removeFavorite_challengeNotFound_404() {
        String challengeId = "not-found-id";
        String userId = "321e4567-e89b-12d3-a456-426614174000";
        String authHeader = "Bearer token";

        when(challengeJwtFacade.getUserUuIdFromAuthenticationHeader(authHeader)).thenReturn(userId);
        when(favoriteService.removeChallengeFromFavorites(challengeId, userId))
                .thenReturn(Mono.error(new ChallengeNotFoundException("Challenge not found")));

        Mono<ResponseEntity<FavoriteDto>> result = favoriteController.removeFavorite(challengeId, authHeader);

        StepVerifier.create(result)
                .expectError(ChallengeNotFoundException.class)
                .verify();
    }

    @Test
    void removeFavorite_internalServerError_500() {
        String challengeId = "123e4567-e89b-12d3-a456-426614174000";
        String userId = "321e4567-e89b-12d3-a456-426614174000";
        String authHeader = "Bearer token";

        when(challengeJwtFacade.getUserUuIdFromAuthenticationHeader(authHeader)).thenReturn(userId);
        when(favoriteService.removeChallengeFromFavorites(challengeId, userId))
                .thenReturn(Mono.error(new InternalServerErrorException("Internal error")));

        Mono<ResponseEntity<FavoriteDto>> result = favoriteController.removeFavorite(challengeId, authHeader);

        StepVerifier.create(result)
                .expectError(InternalServerErrorException.class)
                .verify();
    }
}

// Node: addFavorite_missingAuthHeader_400
// Node: addFavorite_invalidAuthHeader_400
// Node: addFavorite_challengeNotFound_404
// Node: addFavorite_internalServerError_500
// Node: removeFavorite_missingAuthHeader_400
// Node: removeFavorite_challengeNotFound_404
// Node: removeFavorite_internalServerError_500
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


// Node: testAddChallengeToSolved_PropagatesError
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


// Node: createNewResource_InvalidRequest_ReturnsBadRequest
// Node: getResourcesByChallengeId_InvalidId_ReturnsBadRequest
// Node: getResourcesByChallengeId_NoResources_ReturnsNotFoundWithMessage
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


// Node: getAllLanguages_LanguagesExist_LanguagesReturned
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


// Node: testGetTagsByLanguageId_WhenTagsExist_ReturnsOk
// Node: testGetTagsByLanguageId_WhenNoTagsExist_Returns404
// Node: testGetTagsByLanguageId_WhenErrorOccurs_Returns500
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


// Node: getRelatedChallenges_NotFound_Returns404
// Node: deleteOneChallenge_notFound
// Node: addChallengeToBookmarks_ChallengeNotFound_Returns404
// Node: removeChallengeFromBookmarks_ChallengeNotFound_Returns404
// Node: client
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

// Node: getAllSubmissions_returnsSubmissions
// Node: getAllSubmissions_returns200WithEmptyArrayWhenNoSubmissions
// Node: getAllSubmissions_returns400WhenUserIdIsMalformed_byService
// Node: getAllSubmissions_returns500IfUnexpectedError
// Node: postSubmission_returns200_whenServiceSucceeds
// Node: postSubmission_returns400_whenRequestIsInvalid
// Node: postSubmission_returns409_whenSubmissionIsUnmodifiable
// Node: postSubmission_returns400_whenBodyContainsInvalidUUID
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

// Node: testDevProfile_OKWithoutAuthentication
// Node: equalTo
// Node: shouldReturnNotFoundForInvalidChallengeId
// Node: shouldReturnOkForValidChallengeId
// Node: getChallengesByPages_ValidPageParameters_ChallengesReturned
// Node: getChallengesByPages_NullPageParameters_ChallengesReturned
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

// Node: testConvertIdTagFromTag_TagDocumentNotFound
// Node: getValidatedTags_notFound_test
// Node: getValidatedTags_duplicateIds_test
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

// Node: getChallengeByIdWhenNonexistentIdThenReturnsError_test
// Node: updateResourceByUuid_Success
// Node: updateResourceByUuid_ResourceNotFound
// Node: addChallenge_test_invalidTags
// Node: deleteChallengeById_NotFound
// Node: getChallengesByTopic_WhenErrorOccurs_ReturnsError
// Node: addChallengeToBookmarks_WhenChallengeUuidNotValid_ReturnsError
// Node: addChallengeToSolved_WhenChallengeUuidNotValid_ReturnsError
// Node: addChallengeToBookmarks_WhenUserUuidNotValid_ReturnsError
// Node: addChallengeToBookmarks_WhenChallengeUuidIsNull_ReturnsError
// Node: addChallengeToBookmarks_WhenUserUuidIsNull_ReturnsError
// Node: addChallengeToBookmarks_WhenChallengeNotFound_ReturnsError
// Node: addChallengeToSolved_WhenChallengeNotFound_ReturnsError
// Node: addChallengeToBookmarks_WhenUserNotFound_ReturnsError
// Node: addChallengeToBookmarks_WhenUserServiceReturnsCustomBadRequestException_ReturnsError
// Node: addChallengeToBookmarks_WhenUserServiceReturnsCustomInternalServerErrorException_ReturnsError
// Node: addChallengeToBookmarks_WhenUserServiceReturnsAnyException_ReturnsError
// Node: removeChallengeFromBookmarks_WhenChallengeUuidNotValid_ReturnsError
// Node: removeChallengeFromBookmarks_WhenUserUuidNotValid_ReturnsError
// Node: removeChallengeFromBookmarks_WhenChallengeUuidIsNull_ReturnsError
// Node: removeChallengeFromBookmarks_WhenUserUuidIsNull_ReturnsError
// Node: removeChallengeFromBookmarks_WhenChallengeNotFound_ReturnsError
// Node: removeChallengeFromBookmarks_WhenUserNotFound_ReturnsError
// Node: removeChallengeFromBookmarks_WhenUserServiceReturnsCustomBadRequestException_ReturnsError
// Node: removeChallengeFromBookmarks_WhenUserServiceReturnsCustomInternalServerErrorException_ReturnsError
// Node: removeChallengeFromBookmarks_WhenUserServiceReturnsAnyException_ReturnsError
// Node: updateChallengeWhenChallengeDoesNotExist_returnsError_test
// Node: updateChallengeWhenLanguageDoesNotExist_returnsError_test
// Node: updateChallengeWhenChallengeIdNotValid_returnError_test
// Node: updateChallengeWhenChallengeUuidIsNull_ReturnsError
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



// Node: shouldPropagateErrorIfRepositoryFails
// Node: shouldPropagateErrorWhenRepositoryFails
// Node: getAllLanguages_cacheTest
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


// Node: addChallengeToFavorites_WhenChallengeUuidNotValid_ReturnsError
// Node: addChallengeToFavorites_WhenUserUuidNotValid_ReturnsError
// Node: addChallengeToFavorites_WhenChallengeUuidIsNull_ReturnsError
// Node: addChallengeToFavorites_WhenUserUuidIsNull_ReturnsError
// Node: addChallengeToFavorites_WhenChallengeNotFound_ReturnsError
// Node: addChallengeToFavorites_WhenUserNotFound_ReturnsError
// Node: addChallengeToFavorites_WhenUserServiceReturnsCustomBadRequestException_ReturnsError
// Node: addChallengeToFavorites_WhenUserServiceReturnsCustomInternalServerErrorException_ReturnsError
// Node: addChallengeToFavorites_WhenUserServiceReturnsAnyException_ReturnsError
// Node: removeChallengeFromFavorites_WhenChallengeUuidNotValid_ReturnsError
// Node: removeChallengeFromFavorites_WhenUserUuidNotValid_ReturnsError
// Node: removeChallengeFromFavorites_WhenChallengeUuidIsNull_ReturnsError
// Node: removeChallengeFromFavorites_WhenUserUuidIsNull_ReturnsError
// Node: removeChallengeFromFavorites_WhenChallengeNotFound_ReturnsError
// Node: removeChallengeFromFavorites_WhenUserNotFound_ReturnsError
// Node: removeChallengeFromFavorites_WhenUserServiceReturnsCustomBadRequestException_ReturnsError
// Node: removeChallengeFromFavorites_WhenUserServiceReturnsCustomInternalServerErrorException_ReturnsError
// Node: removeChallengeFromFavorites_WhenUserServiceReturnsAnyException_ReturnsError
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


// Node: getResourcesByChallengeId_WhenIdIsNull_ThrowsBadRequestException
// Node: getResourcesByChallengeId_WhenRepositoryFails_ThrowsInternalServerErrorException
// Node: getResourcesByChallengeId_WhenResourceNotFound_PropagatesException
package com.itachallenge.challenge.config.dbchangelog;

import com.mongodb.client.result.UpdateResult;
import com.mongodb.reactivestreams.client.MongoClient;
import com.mongodb.reactivestreams.client.MongoCollection;
import com.mongodb.reactivestreams.client.MongoDatabase;
import org.bson.Document;
import org.bson.conversions.Bson;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.reactivestreams.Publisher;
import org.springframework.data.mongodb.core.ReactiveMongoTemplate;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.data.mongodb.core.query.Update;
import reactor.core.publisher.Mono;

import static org.mockito.Mockito.*;
import static org.springframework.data.mongodb.core.query.Criteria.where;
import static reactor.core.publisher.Mono.empty;
import static reactor.core.publisher.Mono.just;

class DatabaseUpdaterUnitTest {

    private static final String COLLECTION_NAME = "mongockDemo";
    private static final String FIELD_NAME = "language_name";
    private static final String NEW_FIELD_NAME = "Language Name Updated";
    private static final String STATE_FIELD = "State";
    @Mock
    private MongoDatabase mongoDatabase;

    @Mock
    private ReactiveMongoTemplate reactiveMongoTemplate;
    @Mock
    MongoClient mongoClient;

    @InjectMocks
    private DatabaseUpdater databaseUpdater;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
    }

    @DisplayName("Test execution method - in DatabaseUpdater")
    @Test
    void executionTest() {

        ReactiveMongoTemplate reactiveMongoTemplateMock = mock(ReactiveMongoTemplate.class);
        MongoCollection<Document> mongoCollection = mock(MongoCollection.class);


        UpdateResult updateResult = mock(UpdateResult.class);
        Publisher<UpdateResult> updateResultPublisher = Mono.just(updateResult);

        // Configurar mocks para MongoClient y MongoDatabase
        when(mongoClient.getDatabase("challenges")).thenReturn(mongoDatabase);
        when(mongoDatabase.getCollection(COLLECTION_NAME)).thenReturn(mongoCollection);
        when(mongoCollection.updateMany(any(Bson.class), any(Bson.class))).thenReturn(updateResultPublisher);
        when(reactiveMongoTemplateMock.updateMulti(any(), any(), eq(COLLECTION_NAME))).thenReturn(empty());

        DatabaseUpdater databaseUpdater = new DatabaseUpdater(reactiveMongoTemplateMock);
        databaseUpdater.execution(mongoClient);

        verify(mongoCollection).updateMany(any(Bson.class), any(Bson.class));
        verify(reactiveMongoTemplateMock, times(1)).updateMulti(any(Query.class), any(Update.class), eq(COLLECTION_NAME));
    }

    @DisplayName("Test rollBackExecution method - in DatabaseUpdater")
    @Test
    void rollBackExecutionTest() {

        ReactiveMongoTemplate reactiveMongoTemplateMock = mock(ReactiveMongoTemplate.class);
        MongoCollection<Document> mongoCollection = mock(MongoCollection.class);


        UpdateResult updateResult = mock(UpdateResult.class);
        Publisher<UpdateResult> updateResultPublisher = just(updateResult);

        when(mongoClient.getDatabase("challenges")).thenReturn(mongoDatabase);
        when(mongoDatabase.getCollection("mongockDemo")).thenReturn(mongoCollection);
        when(mongoCollection.updateMany((Bson) any(), (Bson) any())).thenReturn(updateResultPublisher);
        when(reactiveMongoTemplateMock.updateMulti(any(), any(), eq("mongockDemo"))).thenReturn(empty());

        DatabaseUpdater databaseUpdater = new DatabaseUpdater(reactiveMongoTemplateMock);
        databaseUpdater.rollBackExecution(mongoClient);

        verify(mongoCollection).updateMany((Bson) any(), (Bson) any());

    }

    @Test
    void updateFieldInCollectionTest() {

        MongoCollection<Document> mongoCollection = mock(MongoCollection.class);
        Bson filter = new Document(FIELD_NAME, new Document("$exists", true));
        Bson update = new Document("$rename", new Document(FIELD_NAME, NEW_FIELD_NAME));
        UpdateResult updateResult = mock(UpdateResult.class);
        Publisher<UpdateResult> updateResultPublisher = Mono.just(updateResult);

        when(mongoClient.getDatabase("challenges")).thenReturn(mongoDatabase);
        when(mongoDatabase.getCollection(COLLECTION_NAME)).thenReturn(mongoCollection);
        when(mongoCollection.updateMany(filter, update)).thenReturn(updateResultPublisher);

        databaseUpdater.updateFieldInCollection(mongoClient);

        verify(mongoCollection).updateMany(filter, update);
    }

    @Test
    void rollbackUpdateFieldInCollectionTest() {

        MongoCollection<Document> mongoCollection = mock(MongoCollection.class);
        Bson filter = new Document(NEW_FIELD_NAME, new Document("$exists", true));
        Bson update = new Document("$rename", new Document(NEW_FIELD_NAME, FIELD_NAME));
        UpdateResult updateResult = mock(UpdateResult.class);
        Publisher<UpdateResult> updateResultPublisher = Mono.just(updateResult);

        when(mongoClient.getDatabase("challenges")).thenReturn(mongoDatabase);
        when(mongoDatabase.getCollection(COLLECTION_NAME)).thenReturn(mongoCollection);
        when(mongoCollection.updateMany(filter, update)).thenReturn(updateResultPublisher);

        databaseUpdater.rollbackUpdateFieldInCollection(mongoClient);
        verify(mongoCollection).updateMany(filter, update);
    }

    @Test
    void addFieldToAllDocumentsTest() {

        Query query = Query.query(where(FIELD_NAME).exists(true));
        Update update = new Update().set(STATE_FIELD, "ACTIVE");

        UpdateResult updateResult = UpdateResult.acknowledged(1, 1L, null);

        when(reactiveMongoTemplate.updateMulti(query, update, COLLECTION_NAME))
                .thenReturn(Mono.just(updateResult));

        databaseUpdater.addFieldToAllDocuments(reactiveMongoTemplate);
        verify(reactiveMongoTemplate, times(1)).updateMulti(query, update, COLLECTION_NAME);
    }


    @Test
    void removeFieldToAllDocumentsTest() {

        Query query = Query.query(where(FIELD_NAME).exists(true));
        Update update = new Update().unset(STATE_FIELD);

        when(reactiveMongoTemplate.updateMulti(query, update, COLLECTION_NAME))
                .thenReturn(Mono.just(UpdateResult.acknowledged(1, 1L, null)));

        databaseUpdater.removeFieldToAllDocuments(reactiveMongoTemplate);
        verify(reactiveMongoTemplate, times(1)).updateMulti(query, update, COLLECTION_NAME);
    }

}

// Node: rollBackExecutionTest
package com.itachallenge.challenge.config.dbchangelog;

import com.itachallenge.challenge.document.LanguageDocument;
import com.mongodb.reactivestreams.client.MongoCollection;
import com.mongodb.reactivestreams.client.MongoDatabase;
import org.bson.Document;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.data.mongodb.core.ReactiveMongoTemplate;
import org.springframework.data.mongodb.core.query.Query;
import reactor.core.publisher.Mono;

import static org.mockito.Mockito.*;

class DatabaseInitializerUnitTest {

    @Mock
    private MongoDatabase mongoDatabase;

    @Mock
    private ReactiveMongoTemplate reactiveMongoTemplate;

    private DatabaseInitializer databaseInitializer;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
        databaseInitializer = new DatabaseInitializer();
    }

    @Test
    void testCreateCollection() {
        when(mongoDatabase.createCollection(any())).thenReturn(Mono.empty());

        databaseInitializer.createCollection(mongoDatabase);

        verify(mongoDatabase, times(1)).createCollection(any());
    }

    @Test
    void testRollbackBeforeExecution() {
        MongoCollection<Document> mongoCollection = Mockito.mock(MongoCollection.class);

        when(mongoDatabase.getCollection(anyString())).thenReturn(mongoCollection);

        when(mongoCollection.drop()).thenReturn(Mono.empty());

        databaseInitializer.rollbackBeforeExecution(mongoDatabase);

        verify(mongoCollection, times(1)).drop();
    }

    @Test
    void testExecution() {
        when(reactiveMongoTemplate.save(any(LanguageDocument.class), any())).thenReturn(Mono.just(new LanguageDocument()));

        databaseInitializer.execution(reactiveMongoTemplate);

        verify(reactiveMongoTemplate, times(1)).save(any(LanguageDocument.class), any());
    }

    @Test
    void testRollback() {
        when(reactiveMongoTemplate.remove(any(Query.class), anyString())).thenReturn(Mono.empty());

        databaseInitializer.rollback(reactiveMongoTemplate);

        verify(reactiveMongoTemplate, times(1)).remove(any(Query.class), anyString());
    }
}

// Node: testCreateCollection
// Node: testExecution
// Node: testRollback
// Node: exchangeCodeForToken
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


// Node: handleTokenError
// Node: validateTokenWithGithub
// Node: handleUnexpectedError
package com.itachallenge.auth.service;

import reactor.core.publisher.Mono;

import java.util.Map;

public interface IAuthService {

    Mono<Map<String, Object>> validateTokenWithGithub(String token);
    Mono<String> exchangeCodeForToken(String code);

}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-auth/src/main/java/com/itachallenge/auth/service/IAuthService.java:IAuthService.<init>
// Node: SwitchRoleRequest
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


// Node: authenticateWithGithub_ValidCode_ReturnsJwt
// Node: authenticateWithGithub_InvalidCode_ReturnsUnauthorized
// Node: isUnauthorized
// Node: authenticateWithGithub_TokenExchangeError_ReturnsInternalServerError
// Node: authenticateWithGithub_TokenValidationError_ReturnsInternalServerError
// Node: authenticateWithGithub_UserDoesNotExist_ReturnsForbidden
// Node: isForbidden
// Node: doesNotExist
// Node: authenticateWithGithub_UserValidationError_ReturnsInternalServerError
// Node: authenticateWithGithub_MissingRequestBody_ReturnsBadRequest
// Node: logout_ValidToken_ShouldReturn200
// Node: doNothing
// Node: logout_ExpiredToken_ShouldReturn200
// Node: doThrow
// Node: logout_TokenJustWithinTry_ShouldReturn200
// Node: logout_InvalidToken_ShouldReturn401
// Node: logout_EmptyAuthorizationHeader_ShouldReturn401
// Node: logout_MalformedAuthorizationHeader_ShouldReturn401
// Node: logout_MissingAuthorizationHeader_ShouldReturn401
// Node: switchRole_WithValidTokenAndValidRole_ReturnsNewToken
// Node: switchRole_WithExpiredToken_Returns200WithMessage
// Node: switchRole_WithInvalidToken_Returns401
// Node: switchRole_WithSameRole_Throws400
// Node: switchRole_MissingAuthorizationHeader_Returns401
