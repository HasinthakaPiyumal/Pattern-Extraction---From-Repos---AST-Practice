// Cluster 8

// Node: setUp
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


// Node: UserClientImpl
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

// Node: AuthClientImpl
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


// Node: ChallengeClientImpl
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

// Node: openMocks
// Node: forEach
// Node: DisplayName
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


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/userinteraction/service/bookmark/BookmarkServiceImpl.java:BookmarkServiceImpl.<init>
// Node: BookmarkServiceImpl
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


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/userinteraction/service/favorite/FavoriteServiceImpl.java:FavoriteServiceImpl.<init>
// Node: FavoriteServiceImpl
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


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/service/ExternalGithubServiceImpl.java:ExternalGithubServiceImpl.<init>
// Node: ExternalGithubServiceImpl
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


// Node: tearDown
// Node: close
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


package com.itachallenge.user.exception;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.mock;

import com.itachallenge.githubcore.exception.GithubUnavailableException;
import com.itachallenge.user.dto.APIErrorResponse;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;

import jakarta.validation.ConstraintViolationException;

import java.net.ConnectException;
import java.net.SocketTimeoutException;
import java.util.Objects;

class UserGlobalExceptionHandlerTest {

    private UserGlobalExceptionHandler exceptionHandler;

    @BeforeEach
    void setUp() {
        exceptionHandler = new UserGlobalExceptionHandler();
    }

    @Test
    void testHandleAny() {
        Exception exception = new Exception("Unexpected Error");
        ResponseEntity<String> response = exceptionHandler.handleAny(exception);

        assertEquals(HttpStatus.INTERNAL_SERVER_ERROR, response.getStatusCode());
        assertTrue(Objects.requireNonNull(response.getBody()).contains("Unexpected error happened."));
    }

    @Test
    void testHandleIllegalArgument() {
        IllegalArgumentException exception = new IllegalArgumentException("Invalid argument");
        ResponseEntity<String> response = exceptionHandler.handleIllegalArgument(exception);

        assertEquals(HttpStatus.NOT_FOUND, response.getStatusCode());
        assertEquals("Invalid argument", response.getBody());
    }

    @Test
    void testHandleValidationExceptions() {
        ConstraintViolationException exception = new ConstraintViolationException("Validation failed", null);
        ResponseEntity<String> response = exceptionHandler.handleValidationExceptions(exception);

        assertEquals(HttpStatus.BAD_REQUEST, response.getStatusCode());
        assertEquals("Validation failed", response.getBody());
    }

    @Test
    void testHandleTypeMismatchException() {
        MethodArgumentTypeMismatchException exception = mock(MethodArgumentTypeMismatchException.class);
        ResponseEntity<String> response = exceptionHandler.handleTypeMismatchException(exception);

        assertEquals(HttpStatus.BAD_REQUEST, response.getStatusCode());
        assertEquals("Invalid parameter format.", response.getBody());
    }

    @Test
    void testHandleBadRequestException() {
        BadRequestException exception = new BadRequestException("Bad request error");
        ResponseEntity<String> response = exceptionHandler.handleBadRequestException(exception);

        assertEquals(HttpStatus.BAD_REQUEST, response.getStatusCode());
        assertEquals("Bad request error", response.getBody());
    }

    @Test
    void testHandleDatabaseException() {
        DatabaseException exception = new DatabaseException("Database connection failed");
        ResponseEntity<String> response = exceptionHandler.handleDatabaseException(exception);

        assertEquals(HttpStatus.INTERNAL_SERVER_ERROR, response.getStatusCode());
        assertEquals("Database error: Database connection failed", response.getBody());
    }

    @Test
    void testHandleNotFoundException() {
        NotFoundException exception = new NotFoundException("Resource not found");
        ResponseEntity<String> response = exceptionHandler.handleNotFoundException(exception);

        assertEquals(HttpStatus.NOT_FOUND, response.getStatusCode());
        assertEquals("Resource not found", response.getBody());
    }

    @Test
    void testHandleUnmodifiableSolutionException(){
        String message = "There's an existing solution with status 'SUBMITTED_COMPLETE'.";
        UnmodificableSolutionException exception = new UnmodificableSolutionException(message);
        ResponseEntity<String> response = exceptionHandler.handleUnmodifiableSolutionException(exception);

        assertEquals(HttpStatus.CONFLICT, response.getStatusCode());
        assertEquals(message, response.getBody());
    }

    @Test
    void testHandleUsernameAlreadyExistsException() {
        String username = "alfonso79";
        UsernameAlreadyExistsException exception = new UsernameAlreadyExistsException(username);
        ResponseEntity<String> response = exceptionHandler.handleUsernameAlreadyExistsException(exception);

        assertEquals(HttpStatus.CONFLICT, response.getStatusCode());
        assertEquals("The username 'alfonso79' is already registered.", response.getBody());
    }


    @Test
    void handleGithubUnavailable_shouldReturn503() {
        Throwable connectCause = new ConnectException("Connection refused");
        GithubUnavailableException ex = new GithubUnavailableException("Service error ocurred.", connectCause);

        ResponseEntity<APIErrorResponse> response = exceptionHandler.handleGithubUnavailable(ex);

        assertEquals(HttpStatus.SERVICE_UNAVAILABLE, response.getStatusCode(),
                "The handler must return HTTP 503 for a ConnectException cause.");
        assertTrue(Objects.requireNonNull(response.getBody()).getMessage().contains("unavailable"),
                "The secured message should indicate service unavailability.");
    }

    @Test
    void handleGithubUnavailable_shouldReturn504() {
        Throwable timeoutCause = new SocketTimeoutException("Read timed out");
        GithubUnavailableException ex = new GithubUnavailableException("Service error ocurred.", timeoutCause);

        ResponseEntity<APIErrorResponse> response = exceptionHandler.handleGithubUnavailable(ex);

        assertEquals(HttpStatus.GATEWAY_TIMEOUT, response.getStatusCode(),
        "The handler must return HTTP 504 for a SocketTimeoutException cause.");
        assertTrue(Objects.requireNonNull(response.getBody()).getMessage().contains("timed out"),
                "The secured message should indicate a timeout.");
    }

    @Test
    void handleGithubUnavailable_shouldReturn503ForOtherCauses() {
        GithubUnavailableException ex = new GithubUnavailableException("Unknown error.");

        ResponseEntity<APIErrorResponse> response = exceptionHandler.handleGithubUnavailable(ex);

        assertEquals(HttpStatus.SERVICE_UNAVAILABLE, response.getStatusCode(),
                "The handler must return HTTP 503 for other types of causes (not recognized or null).");
        assertTrue(Objects.requireNonNull(response.getBody()).getMessage().contains("external service error"),
                "The secured message should indicate an external service error.");
    }

}



// Node: UserGlobalExceptionHandler
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

// Node: bindToController
// Node: controllerAdvice
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


// Node: deleteAll
// Node: block
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


package com.itachallenge.user.validator;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;

import jakarta.validation.ConstraintValidatorContext;
import java.util.regex.Pattern;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class GenericUUIDValidatorTest {

    private GenericUUIDValidator validator;

    @Mock
    private ConstraintValidatorContext context;

    @Mock
    private ConstraintValidatorContext.ConstraintViolationBuilder violationBuilder;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
        validator = new GenericUUIDValidator();

        // Simulate @Value injection manually
        String uuidRegex = "^[a-fA-F0-9]{24}$"; // Example MongoDB ObjectId pattern
        validator.UUID_PATTERN = Pattern.compile(uuidRegex);

        when(context.buildConstraintViolationWithTemplate(anyString())).thenReturn(violationBuilder);
    }

    @Test
    void testValidUUID_ShouldReturnTrue() {
        String validUUID = "507f1f77bcf86cd799439011"; // Example valid MongoDB ObjectId

        assertTrue(validator.isValid(validUUID, context));
    }

    @Test
    void testNullUUID_ShouldReturnFalseAndSetMessage() {
        when(context.getDefaultConstraintMessageTemplate()).thenReturn("Invalid UUID");

        boolean result = validator.isValid(null, context);

        assertFalse(result);
        verify(context).disableDefaultConstraintViolation();
        verify(context).buildConstraintViolationWithTemplate("Invalid UUID: value is null");
        verify(violationBuilder).addConstraintViolation();
    }

    @Test
    void testInvalidUUID_ShouldReturnFalseAndSetMessage() {
        when(context.getDefaultConstraintMessageTemplate()).thenReturn("Invalid UUID");
        String invalidUUID = "invalid-uuid-1234";

        boolean result = validator.isValid(invalidUUID, context);

        assertFalse(result);
        verify(context).disableDefaultConstraintViolation();
        verify(context).buildConstraintViolationWithTemplate("Invalid UUID: " + invalidUUID);
        verify(violationBuilder).addConstraintViolation();
    }

    @Test
    void testEmptyUUID_ShouldReturnFalseAndSetMessage() {
        when(context.getDefaultConstraintMessageTemplate()).thenReturn("Invalid UUID");
        String emptyUUID = "";

        boolean result = validator.isValid(emptyUUID, context);

        assertFalse(result);
        verify(context).disableDefaultConstraintViolation();
        verify(context).buildConstraintViolationWithTemplate("Invalid UUID: ");
        verify(violationBuilder).addConstraintViolation();
    }
}



// Node: GenericUUIDValidator
package com.itachallenge.user.validator;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import javax.validation.ConstraintValidatorContext;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class GithubUsernameValidatorTest {

    private GithubUsernameValidator validator;
    private ConstraintValidatorContext context;

    @BeforeEach
    void setUp() {
        validator = new GithubUsernameValidator();
        context = mock(ConstraintValidatorContext.class);
    }

    @Test
    void shouldReturnTrueForValidUsername() {
        assertTrue(validator.isValid("validUsername", context));
        assertTrue(validator.isValid("user-123", context));
        assertTrue(validator.isValid("A1-B2-C3", context));
    }

    @Test
    void shouldReturnFalseForNullUsername() {
        assertFalse(validator.isValid(null, context));
    }

    @Test
    void shouldReturnFalseForEmptyString() {
        assertFalse(validator.isValid("", context));
    }

    @Test
    void shouldReturnFalseForTooLongUsername() {
        String longUsername = "a".repeat(40);
        assertFalse(validator.isValid(longUsername, context));
    }

    @Test
    void shouldReturnFalseForInvalidCharacters() {
        assertFalse(validator.isValid("invalid_username!", context));
        assertFalse(validator.isValid("invalid@username", context));
        assertFalse(validator.isValid("user name", context));
    }

    @Test
    void shouldReturnFalseForUsernameStartingOrEndingWithHyphen() {
        assertFalse(validator.isValid("-invalidUser", context));
        assertFalse(validator.isValid("invalidUser-", context));
    }

    @Test
    void shouldReturnTrueForMinimumLengthUsername() {
        assertTrue(validator.isValid("a", context));
    }

    @Test
    void shouldReturnTrueForMaximumLengthUsername() {
        String maxUsername = "a".repeat(39);
        assertTrue(validator.isValid(maxUsername, context));
    }
}



// Node: GithubUsernameValidator
package com.itachallenge.user.filter;

import com.itachallenge.user.config.TomcatConfig;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import static org.mockito.Mockito.*;

import java.io.IOException;

import static org.junit.jupiter.api.Assertions.assertThrows;


class ContentLengthFilterTest {

    @Mock
    private TomcatConfig tomcatConfig;

    @Mock
    private HttpServletRequest request;

    @Mock
    private HttpServletResponse response;

    @Mock
    private FilterChain filterChain;

    @InjectMocks
    private ContentLengthFilter filter;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
    }

    @Test
    void doFilter_whenContentLengthExceedsLimit_thenThrowServletException() {
        when(request.getContentLength()).thenReturn(100);
        when(tomcatConfig.getMaxHttpFormPostSize()).thenReturn(50);

        assertThrows(ServletException.class, () -> filter.doFilter(request, response, filterChain));
    }

    @Test
    void doFilter_whenContentLengthIsWithinLimit_thenProceedWithChain() throws ServletException, IOException {
        when(request.getContentLength()).thenReturn(30);
        when(tomcatConfig.getMaxHttpFormPostSize()).thenReturn(50);

        filter.doFilter(request, response, filterChain);

        verify(filterChain, times(1)).doFilter(request, response);
    }
}

// Node: getTagsByLanguageId
// Node: existsByUuid
// Node: saveAll
// Node: existsByChallengeTitle
package com.itachallenge.challenge.repository;

import com.itachallenge.challenge.document.SolutionDocument;
import org.springframework.data.mongodb.repository.ReactiveMongoRepository;
import reactor.core.publisher.Mono;

import java.util.UUID;

public interface SolutionRepository extends ReactiveMongoRepository<SolutionDocument, UUID> {

    Mono<Boolean> existsByUuid(UUID uuid);

    Mono<SolutionDocument> findByUuid(UUID uuid);

    Mono<Void> deleteByUuid(UUID uuid);
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/repository/SolutionRepository.java:SolutionRepository.<init>
package com.itachallenge.challenge.repository;

import com.itachallenge.challenge.document.ResourceDocument;
import com.itachallenge.challenge.enums.ResourceContentType;
import com.itachallenge.challenge.enums.Topic;
import org.springframework.data.repository.reactive.ReactiveSortingRepository;
import org.springframework.stereotype.Repository;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.UUID;

@Repository
public interface ResourceRepository extends ReactiveSortingRepository<ResourceDocument, UUID> {

    Mono<Boolean> existsByResourceId(UUID uuid);
    Mono<ResourceDocument> findByResourceId(UUID uuid);
    Flux<ResourceDocument> findByTopic(Topic topic);
    Flux<ResourceDocument> findByContentType(ResourceContentType contentType);


    Mono<Long> count();
    Mono<Void> deleteByResourceId(UUID uuid);
    Mono<ResourceDocument> save(ResourceDocument resource);
    Flux<ResourceDocument> saveAll(Flux<ResourceDocument> resourceDocumentFlux);
    Mono<Void> deleteAll();

    Flux<ResourceDocument> findByChallengeIdsContaining(UUID challengeId);
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/repository/ResourceRepository.java:ResourceRepository.<init>
// Node: existsByResourceId
// Node: deleteByResourceId
package com.itachallenge.challenge.repository;

import com.itachallenge.challenge.document.TagDocument;
import org.springframework.data.mongodb.repository.ReactiveMongoRepository;
import org.springframework.stereotype.Repository;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.UUID;

@Repository
public interface TagRepository extends ReactiveMongoRepository<TagDocument, UUID> {
    Flux<TagDocument> findByLanguageId(UUID languageId);
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/repository/TagRepository.java:TagRepository.<init>
// Node: findByLanguageId
// Node: doOnNext
// Node: convertIdTagFromTagDocument
package com.itachallenge.challenge.service;

import com.itachallenge.challenge.document.TagDocument;
import com.itachallenge.challenge.dto.GenericResultDto;
import com.itachallenge.challenge.dto.TagDto;
import reactor.core.publisher.Mono;

import java.util.List;
import java.util.Set;
import java.util.UUID;

public interface ITagService {

    Mono<GenericResultDto<TagDto>> getTagsByLanguageId(UUID LanguageId);
    Set<TagDocument> convertIdTagFromTagDocument(List<UUID> tags);
    Mono<Boolean> getValidatedTags(List<UUID> tagIds);
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/service/ITagService.java:ITagService.<init>
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

// Node: getCache
// Node: computeIfAbsent
// Node: getCacheNames
// Node: keySet
// Node: toMillis
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


// Node: createCollection
// Node: await
// Node: rollbackBeforeExecution
// Node: getCollection
// Node: drop
// Node: execution
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


// Node: DatabaseUpdater
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


// Node: SubmissionDocument
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


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/submission/enums/SubmissionStatusTest.java:SubmissionStatusTest.<init>
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

// Node: getRequestValues
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


// Node: ChallengeSolvedController
// Node: TagDto
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


// Node: TagDocument
// Node: asList
// Node: blockLast
// Node: testDB
// Node: getTagName
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

// Node: existsByIdTest
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

// Node: existsByUuidTest
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


// Node: existsByResourceIdTest
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

// Node: findByChallengeTitle_matchingTitle_test
// Node: findByChallengeTitle_nonMatchingTitle_test
package com.itachallenge.challenge.document;

import org.junit.jupiter.api.Test;

import java.util.HashSet;
import java.util.Set;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

public class TagTest {

    @Test
    void getTestName() {
        String tagNameTest = "POO";
        TagDocument tag = new TagDocument(null, tagNameTest, null, UUID.randomUUID());
        assertEquals(tagNameTest, tag.getTagName());
    }

    @Test
    void getDescriptionTest() {
        String tagDescriptionTest = "Programació orientada a objectes";
        TagDocument tag = new TagDocument(null, "POO", tagDescriptionTest, UUID.randomUUID());
        assertEquals(tagDescriptionTest, tag.getTagDescription());
    }

    @Test
    void setTestName() {
        String firstTagName = "POO";
        String tagNameTest = "TEST";
        TagDocument tag = new TagDocument(null, firstTagName, null, UUID.randomUUID());
        tag.setTagName(tagNameTest);
        assertEquals(tagNameTest, tag.getTagName());
    }

    @Test
    void setDescriptionTest() {
        String firstTagDescription = "Programació orientada a objectes";
        String tagDescriptionTest = "TEST";
        TagDocument tag = new TagDocument(null, "POO", firstTagDescription, UUID.randomUUID());
        tag.setTagDescription(tagDescriptionTest);
        assertEquals(tagDescriptionTest, tag.getTagDescription());
    }

    @Test
    void fullConstructorTest() {
        UUID id = UUID.randomUUID();
        String name = "POO";
        String desc = "Programació orientada a objectes";

        TagDocument tag = new TagDocument(id, name, desc, UUID.randomUUID());

        assertEquals(id, tag.getIdTag());
        assertEquals(name, tag.getTagName());
        assertEquals(desc, tag.getTagDescription());
    }
    
}


// Node: getTestName
// Node: getDescriptionTest
// Node: getTagDescription
// Node: setTestName
// Node: setTagName
// Node: setDescriptionTest
// Node: setTagDescription
// Node: fullConstructorTest
// Node: getIdTag
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

// Node: onError
// Node: countDown
// Node: onComplete
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

// Node: getLanguageMocked
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

// Node: testConvertIdTagFromTag_Document_Success
// Node: testGetTagsByLanguageId
// Node: getTagsByLanguageId_nullLanguageId_test
package com.itachallenge.challenge.service;

import com.itachallenge.challenge.document.ChallengeDocument;
import com.itachallenge.challenge.document.SolutionDocument;
import com.itachallenge.challenge.dto.*;

import com.itachallenge.challenge.helper.DocumentToDtoConverter;
import com.itachallenge.challenge.repository.ChallengeRepository;
import com.itachallenge.challenge.repository.SolutionRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.cache.Cache;
import org.springframework.cache.CacheManager;
import org.springframework.cache.annotation.EnableCaching;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

import java.util.*;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;
import static org.mockito.Mockito.verifyNoMoreInteractions;

@SpringBootTest
@EnableCaching
class ChallengeServiceImplCacheTest {

    @MockBean private ChallengeRepository challengeRepository;
    @MockBean private ILanguageService iLanguageService;
    @MockBean private IUserService userService;
    @MockBean private ITagService tagService;
    @MockBean private SolutionRepository solutionRepository;
    @MockBean private DocumentToDtoConverter<ChallengeDocument, ChallengeDto> challengeConverter;
    @MockBean private DocumentToDtoConverter<SolutionDocument, SolutionDto> solutionConverter;

    @Autowired
    private CacheManager cacheManager;

    @Autowired
    private IChallengeService challengeService;

    @BeforeEach
    void setUp() {
        cacheManager.getCacheNames().forEach(name -> {
            Cache cache = cacheManager.getCache(name);
            if (cache != null) cache.clear();
        });
    }

    @DisplayName("Cache - getChallengeById")
    @Test
    void getChallengeById_cacheTest() {
        // Arrange
        UUID challengeId = UUID.randomUUID();
        ChallengeDocument challengeDocument = new ChallengeDocument();
        ChallengeDto challengeDto = new ChallengeDto();
        challengeDto.setChallengeId(challengeId);
        challengeDto.setLevel("EASY");

        when(challengeRepository.findByUuid(challengeId)).thenReturn(Mono.just(challengeDocument).cache());
        when(challengeConverter.convertDocumentToDto(any(), any())).thenReturn(challengeDto);

        // Act - First call
        Mono<ChallengeDto> result1 = challengeService.getChallengeById(challengeId.toString());

        StepVerifier.create(result1)
                .expectNextMatches(dto -> dto.getChallengeId().equals(challengeId) &&
                        dto.getLevel().equals(challengeDto.getLevel()))
                .verifyComplete();

        // Use atLeastOnce instead of times(1)
        verify(challengeRepository, atLeastOnce()).findByUuid(challengeId);

        // Act - Second call (cached)
        Mono<ChallengeDto> result2 = challengeService.getChallengeById(challengeId.toString());

        StepVerifier.create(result2)
                .expectNextMatches(dto -> dto.getChallengeId().equals(challengeId) &&
                        dto.getLevel().equals(challengeDto.getLevel()))
                .verifyComplete();

    }

    @DisplayName("Cache - getAllChallenges")
    @Test
    void getAllChallenges_cacheTest() {
        // Arrange
        int offset = 1;
        int limit = 2;

        ChallengeDocument challenge1 = new ChallengeDocument();
        challenge1.setUuid(UUID.randomUUID());
        ChallengeDocument challenge2 = new ChallengeDocument();
        challenge2.setUuid(UUID.randomUUID());
        ChallengeDocument challenge3 = new ChallengeDocument();
        challenge3.setUuid(UUID.randomUUID());
        ChallengeDocument challenge4 = new ChallengeDocument();
        challenge4.setUuid(UUID.randomUUID());

        ChallengeDto challengeDto1 = new ChallengeDto();
        ChallengeDto challengeDto2 = new ChallengeDto();
        ChallengeDto challengeDto3 = new ChallengeDto();
        ChallengeDto challengeDto4 = new ChallengeDto();

        when(challengeRepository.count()).thenReturn(Mono.just(4L));
        when(challengeRepository.findAllByUuidNotNullExcludingTestingValues())
                .thenReturn(Flux.just(challenge1, challenge2, challenge3, challenge4));
        when(challengeConverter.convertDocumentFluxToDtoFlux(any(), any()))
                .thenReturn(Flux.just(challengeDto1, challengeDto2, challengeDto3, challengeDto4));

        // Act
        Mono<GenericResultDto<ChallengeDto>> result = challengeService.getAllChallenges(offset, limit);

        // Assert
        StepVerifier.create(result)
                .expectNextMatches(dto -> dto.getCount() == 4 && Arrays.equals(dto.getResults(), new ChallengeDto[]{challengeDto1, challengeDto2, challengeDto3, challengeDto4}))
                .expectComplete()
                .verify();

        verify(challengeRepository, times(1)).count();
        verify(challengeRepository, times(1)).findAllByUuidNotNullExcludingTestingValues();
        verify(challengeConverter, times(1)).convertDocumentFluxToDtoFlux(any(), any());

        Mono<GenericResultDto<ChallengeDto>> resultCached = challengeService.getAllChallenges(offset, limit);

        StepVerifier.create(resultCached)
                .expectNextMatches(dto -> dto.getCount() == 4 && Arrays.equals(dto.getResults(), new ChallengeDto[]{challengeDto1, challengeDto2, challengeDto3, challengeDto4}))
                .expectComplete()
                .verify();

        verifyNoMoreInteractions(challengeRepository, challengeConverter);
    }

    @DisplayName("Cache - getSolutions")
    @Test
    void testGetChallengeSolutions_cacheTest() {
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

        when(challengeRepository.findByUuid(challenge.getUuid())).thenReturn(Mono.just(challenge).cache());
        when(solutionRepository.findById(solutionId1)).thenReturn(Mono.just(solution1).cache());
        when(solutionRepository.findById(solutionId2)).thenReturn(Mono.just(solution2).cache());
        when(solutionConverter.convertDocumentFluxToDtoFlux(any(), any())).thenReturn(Flux.fromIterable(expectedSolutions));

        // Act - First call
        Mono<GenericResultDto<SolutionDto>> resultMono = challengeService.getSolutions(challengeStringId, languageStringId);

        StepVerifier.create(resultMono)
                .expectNextMatches(resultDto -> {
                    assertThat(resultDto.getOffset()).isZero();
                    assertThat(resultDto.getLimit()).isEqualTo(expectedSolutions.size());
                    assertThat(resultDto.getCount()).isEqualTo(expectedSolutions.size());
                    return true;
                })
                .verifyComplete();

        verify(challengeRepository, atLeastOnce()).findByUuid(UUID.fromString(challengeStringId));
        verify(solutionRepository, atLeastOnce()).findById(any(UUID.class));
        verify(solutionConverter, atLeastOnce()).convertDocumentFluxToDtoFlux(any(), eq(SolutionDto.class));

        // Act - Cached call
        Mono<GenericResultDto<SolutionDto>> resultCached = challengeService.getSolutions(challengeStringId, languageStringId);

        StepVerifier.create(resultCached)
                .assertNext(actualResult -> {
                    assertThat(actualResult.getCount()).isEqualTo(2);
                    assertThat(actualResult.getResults()).containsExactly(solutionDto1, solutionDto2);
                })
                .verifyComplete();

    }

}

// Node: clear
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



// Node: testGetTagsByLanguageIdUsesCache
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

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/challenge/helper/ResourceHelperTest.java:ResourceHelperTest.<init>
package com.itachallenge.challenge.helper;

import com.itachallenge.challenge.document.LanguageDocument;
import com.itachallenge.challenge.document.TagDocument;
import com.itachallenge.challenge.dto.LanguageDto;
import com.itachallenge.challenge.dto.TagDto;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import reactor.core.publisher.Flux;
import reactor.test.StepVerifier;

import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Assertions.assertEquals;


class TagDocumentToDtoConverterTest {

    private DocumentToDtoConverter<TagDocument, TagDto> mapper;

    private TagDocument tagDocument1;

    private TagDocument tagDocument2;

    private TagDto tagDto1;

    private TagDto tagDto2;


    @BeforeEach
    public void setUp() {
        mapper = new DocumentToDtoConverter<>();

        UUID[] tagsID = new UUID[]{UUID.randomUUID(), UUID.randomUUID()};
        String[] tagsNames = new String[]{"POO", "Refactorizacion"};
        String description = "bla bla bla";
        UUID idLanguage1 = UUID.fromString("7bcf4ad3-092d-4c13-8f78-685c2a8803a9");
        UUID idLanguage2 = UUID.fromString("bf893476-bf0f-464a-927c-4fee3b207123");

        tagDocument1 = new TagDocument(tagsID[0], tagsNames[0], description, idLanguage1);
        tagDocument2 = new TagDocument(tagsID[1], tagsNames[1], description, idLanguage2);

        tagDto1 = new TagDto(tagsID[0], tagsNames[0], description, idLanguage1);
        tagDto2 = new TagDto(tagsID[1], tagsNames[1], description, idLanguage2);

    }

    @Test
    @DisplayName("Conversion from document to dto when the field types and names perfectly match the source")
    void testConvertTagDocumentToTagDto() {

        TagDocument tagDocumentMocked = tagDocument1;
        TagDto resultDto = mapper.convertDocumentToDto(tagDocumentMocked, TagDto.class);
        TagDto expectedDto = tagDto1;


        assertEquals(expectedDto.getTagId(), resultDto.getTagId());
        assertEquals(expectedDto.getTagName(), resultDto.getTagName());
        assertEquals(expectedDto.getTagDescription(), resultDto.getTagDescription());
    }

    @Test
    @DisplayName("Test convertFluxEntityToFluxDto method")
    void testConvertFluxEntityToFluxDto() {
        Flux<TagDocument> documentFlux = Flux.just(tagDocument1, tagDocument2);
        Flux<TagDto> resultFlux = mapper.convertDocumentFluxToDtoFlux(documentFlux, TagDto.class);
        Flux<TagDto> expectedFlux = Flux.just(tagDto1, tagDto2);

        StepVerifier.create(resultFlux)
                .assertNext(tagDto -> {
                    Assertions.assertEquals(tagDto1.getTagId(), tagDto.getTagId());
                    Assertions.assertEquals(tagDto1.getTagName(), tagDto.getTagName());
                    Assertions.assertEquals(tagDto1.getTagDescription(), tagDto.getTagDescription());
                })
                .assertNext(tagDto -> {
                    Assertions.assertEquals(tagDto2.getTagId(), tagDto.getTagId());
                    Assertions.assertEquals(tagDto2.getTagName(), tagDto.getTagName());
                    Assertions.assertEquals(tagDto2.getTagDescription(), tagDto.getTagDescription());
                })
                .expectComplete()
                .verify();

        assertThat(expectedFlux.blockFirst()).usingRecursiveComparison().isEqualTo(resultFlux.blockFirst());
        assertThat(expectedFlux.blockLast()).usingRecursiveComparison().isEqualTo(resultFlux.blockLast());
    }

}



// Node: testConvertTagDocumentToTagDto
// Node: getTagId
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


// Node: buildLanguageDto
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



// Node: testTagDtoAllArgsConstructorAndGetters
// Node: testTagDtoNoArgsConstructorAndSetters
// Node: setTagId
// Node: testJsonSerialization
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

// Node: executionTest
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

// Node: forClass
// Node: dropCollection
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

// Node: DatabaseInitializer
// Node: testRollbackBeforeExecution
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


// Node: ReactiveMongoTemplate
// Node: testCollectionCreation
// Node: getNamespace
// Node: getCollectionName
// Node: testDocumentCreation
// Node: find
// Node: first
// Node: testUpdateOperation
package com.itachallenge.auth.service;

import com.itachallenge.auth.enums.UserRole;
import io.jsonwebtoken.Claims;
import org.springframework.stereotype.Service;

@Service
public class JwtRoleSwitchService {

    private final IAuthJwtFacade authJwtFacade;

    public JwtRoleSwitchService(IAuthJwtFacade authJwtFacade) {
        this.authJwtFacade = authJwtFacade;
    }

    public String switchRole(String token, String requestedRole) {
        Claims claims = authJwtFacade.extractAllClaims(token);
        String currentRole = claims.get("role", String.class);

        UserRole.validateRoleChange(currentRole, requestedRole);

        return authJwtFacade.generateToken(
                claims.getSubject(),
                requestedRole.toUpperCase(),
                claims.get("uuid", String.class)
        );
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-auth/src/main/java/com/itachallenge/auth/service/JwtRoleSwitchService.java:JwtRoleSwitchService.<init>
// Node: JwtRoleSwitchService
package com.itachallenge.auth.service;

import com.itachallenge.auth.exception.InvalidRoleChangeRequestException;
import com.itachallenge.jwtcore.service.IJwtService;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.JwtException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.Mockito.*;

class JwtRoleSwitchServiceTest {

    private JwtRoleSwitchService jwtRoleSwitchService;
    private IAuthJwtFacade authJwtFacade;

    @BeforeEach
    void setUp() {
        authJwtFacade = mock(IAuthJwtFacade.class);
        jwtRoleSwitchService = new JwtRoleSwitchService(authJwtFacade);
    }

    @Test
    void switchRole_validRoleChange_returnsNewToken() {
        String oldToken = "old.token";
        String username = "testuser";
        String uuid = "uuid-1234";
        String currentRole = "USER";
        String requestedRole = "ADMIN";
        String newToken = "new.token";

        Claims claims = mock(Claims.class);
        when(authJwtFacade.extractAllClaims(oldToken)).thenReturn(claims);
        when(claims.getSubject()).thenReturn(username);
        when(claims.get("uuid", String.class)).thenReturn(uuid);
        when(claims.get("role", String.class)).thenReturn(currentRole);
        when(authJwtFacade.generateToken(username, requestedRole.toUpperCase(), uuid)).thenReturn(newToken);

        String result = jwtRoleSwitchService.switchRole(oldToken, requestedRole);

        assertThat(result).isEqualTo(newToken);
        verify(authJwtFacade).extractAllClaims(oldToken);
        verify(authJwtFacade).generateToken(username, requestedRole.toUpperCase(), uuid);
    }

    @Test
    void switchRole_invalidRoleChange_throwsException() {
        String oldToken = "old.token";
        String username = "testuser";
        String uuid = "uuid-1234";
        String currentRole = "USER";
        String requestedRole = "USER";

        Claims claims = mock(Claims.class);
        when(authJwtFacade.extractAllClaims(oldToken)).thenReturn(claims);
        when(claims.getSubject()).thenReturn(username);
        when(claims.get("uuid", String.class)).thenReturn(uuid);
        when(claims.get("role", String.class)).thenReturn(currentRole);

        assertThatThrownBy(() -> jwtRoleSwitchService.switchRole(oldToken, requestedRole))
                .isInstanceOf(InvalidRoleChangeRequestException.class)
                .hasMessageContaining("same as current role");
    }

    @Test
    void switchRole_InvalidRequestedRole_ShouldThrowException() {
        String token = "valid.token";
        String username = "testUser";
        String uuid = "uuid-003";
        String currentRole = "USER";

        Claims claims = mock(Claims.class);
        when(authJwtFacade.extractAllClaims(token)).thenReturn(claims);
        when(claims.getSubject()).thenReturn(username);
        when(claims.get("uuid", String.class)).thenReturn(uuid);
        when(claims.get("role", String.class)).thenReturn(currentRole);

        assertThatThrownBy(() -> jwtRoleSwitchService.switchRole(token, "GUEST"))
                .isInstanceOf(com.itachallenge.auth.exception.InvalidRoleChangeRequestException.class)
                .hasMessage("Requested role change is not allowed.");

    }

    @Test
    void switchRole_InvalidToken_ShouldThrowJwtException() {
        String invalidToken = "not.a.valid.token";

        when(authJwtFacade.extractAllClaims(invalidToken))
                .thenThrow(new JwtException("Invalid or tampered token"));

        assertThatThrownBy(() -> jwtRoleSwitchService.switchRole(invalidToken, "ADMIN"))
                .isInstanceOf(JwtException.class)
                .hasMessageContaining("Invalid or tampered token");
    }
}


