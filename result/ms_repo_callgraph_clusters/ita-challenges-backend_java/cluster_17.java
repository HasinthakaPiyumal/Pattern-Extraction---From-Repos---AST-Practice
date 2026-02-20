// Cluster 17

// Node: of
// Node: now
// Node: eq
// Node: addToFavorites
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


// Node: booleanValue
// Node: FavoriteDocument
// Node: setUuid
// Node: setUserId
// Node: setChallengeId
// Node: addToBookmarks
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


// Node: assertNext
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


// Node: equalsHashCodeAndToString_shouldCoverMainBranches
// Node: getChallengeById
// Node: getAllChallenges
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

// Node: getChallengesByFilter
// Node: getIdLanguage
// Node: getLevel
// Node: getTags
// Node: getOffset
// Node: getLimit
// Node: by
// Node: getRelatedChallenges
// Node: getCount
// Node: getSolutions
// Node: findByUuid
// Node: findAllByUuidNotNullExcludingTestingValues
// Node: count
// Node: deleteByUuid
package com.itachallenge.challenge.repository;

import com.itachallenge.challenge.document.LanguageDocument;
import org.springframework.data.mongodb.repository.ReactiveMongoRepository;
import reactor.core.publisher.Mono;

import java.util.UUID;


public interface LanguageRepository extends ReactiveMongoRepository<LanguageDocument, UUID> {


    Mono<LanguageDocument> findByIdLanguage(UUID id);

    Mono<Void> deleteByIdLanguage(UUID id);

    Mono<LanguageDocument> findFirstByLanguageName(String languageName);

}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/repository/LanguageRepository.java:LanguageRepository.<init>
// Node: findByIdLanguage
// Node: deleteByIdLanguage
package com.itachallenge.challenge.document;

import lombok.*;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
import org.springframework.data.mongodb.core.mapping.Field;
import java.util.UUID;

@Document(collection="languages")
@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
public class LanguageDocument {

    @Id
    @Field(name="id_languages")
    private UUID idLanguage;

    @Field(name="language_name")
    private String languageName;

    @Field(name="language_image")
    private String languageImage;

    public String getLanguageImage() {
        return (languageImage != null) ? languageImage : "https://default-image.com/default.png";
    }

}


// Node: getLanguageImage
// Node: convertDocumentFluxToDtoFlux
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

package com.itachallenge.challenge.service;

import com.itachallenge.challenge.document.ChallengeDocument;
import com.itachallenge.challenge.dto.*;
import com.itachallenge.challenge.enums.Topic;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

public interface IChallengeService {

    Mono<ChallengeDto> getChallengeById(String id);

    Mono<GenericResultDto<SolutionDto>> getSolutions(String idChallenge, String idLanguage);

    Mono<SolutionDto> addSolution(SolutionDto solutionDto);

    Mono<GenericResultDto<ChallengeDto>> getAllChallenges(int offset, int limit);

    Flux<GenericResultDto<ChallengeDto>> getChallengesByFilter(Optional<String> idLanguage,
                                                               Optional<String> level,
                                                               Optional<List<UUID>> tags,
                                                               int offset,
                                                               int limit);

    Mono<GenericResultDto<ChallengeDto>> getRelatedChallenges(String challengeId);

    Mono<String> updateResourceByUuid(String id, Map<String, Object> updates);

    Mono<ChallengeDto> addChallenge(ChallengeCreateDto challengeCreateDto);

    Mono<DeleteResponseDto> deleteChallengeById(String id);

    Mono<ChallengeListDto> getChallengesByTopic(Topic topic, int page, int size);

    Mono<BookmarkDto> addChallengeToBookmarks(String challengeId, String userId);

    Mono<BookmarkDto> removeChallengeFromBookmarks(String challengeId, String userId);

    Mono<ChallengeDto> updateChallenge(String challengeId, ChallengeCreateDto challengeCreateDto);

    Mono<SolvedDto> addChallengeToSolved(String challengeId);
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/service/IChallengeService.java:IChallengeService.<init>
// Node: getLanguages
// Node: fromIterable
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

// Node: zipWith
// Node: intValue
// Node: SolutionDocument
// Node: setIdLanguage
// Node: setSolutions
// Node: setField
// Node: buildChallengeDocument
// Node: DetailDocument
// Node: getChallengeTitle
// Node: level
// Node: creationDate
// Node: detail
// Node: languages
// Node: solutions
// Node: updateChallengeDocument
// Node: setTitle
// Node: setLevel
// Node: setDetail
// Node: setLanguages
// Node: setTags
// Node: getResults
// Node: ofPattern
// Node: LanguageDocument
// Node: usingRecursiveComparison
// Node: ChallengeDto
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


// Node: getChallenges_IncludesTimesFavorite
// Node: timesFavorite
// Node: provideEmptyFields
// Node: setChallengeTitle
// Node: setDescription
// Node: setLanguage
// Node: setSolution
// Node: LanguageDto
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

// Node: findByIdTest
// Node: blockOptional
// Node: ifPresentOrElse
// Node: fail
// Node: deleteByIdTest
// Node: expectComplete
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

// Node: findByUuidTest
// Node: deleteByUuidTest
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

// Node: testDefaultValues
package com.itachallenge.challenge.document;

import org.junit.jupiter.api.Test;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertEquals;

class LanguageTest {

    @Test
    void getIdLanguage() {
        UUID uuid = UUID.fromString("09fabe32-7362-4bfb-ac05-b7bf854c6e0f");
        LanguageDocument language = new LanguageDocument(uuid, null, null);
        assertEquals(uuid, language.getIdLanguage());
    }

    @Test
    void getLanguageName() {
        String languageName = "Javascript";
        LanguageDocument language = new LanguageDocument(null, languageName, null );
        assertEquals(languageName, language.getLanguageName());
    }

    @Test
    void getLanguageImage(){
        String languageImage = "https://res.cloudinary.com/itachallenge/image/upload/v1739361249/language_icon_Javascript_asgn04.svg";
        LanguageDocument language = new LanguageDocument(null, null, languageImage );
        assertEquals(languageImage, language.getLanguageImage());
    }
}


// Node: getLanguageName
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

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/challenge/document/ChallengeTest.java:ChallengeTest.<init>
// Node: ChallengeDocument
// Node: getCreationDate
// Node: truncatedTo
// Node: isEqual
// Node: getDetail
// Node: getTagsTest
// Node: setTagsTest
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

// Node: getTagsByLanguageId_returnsEmptyList_test
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

// Node: getChallengeDtoMocked
// Node: getChallengeById_ValidId_ChallengeFound
// Node: getAllChallenges_ChallengesExist_ChallengesReturned
// Node: expectSubscription
// Node: testGetSolutions
// Node: isZero
// Node: testGetSolutions_InvalidChallengeId
// Node: testGetSolutions_InvalidLanguageId
// Node: testGetSolutions_ChallengeNotFound
// Node: addSolution_ValidChallengeIdAndLanguageId_SolutionAdded
// Node: addChallenge_test_NonExistentLanguage
// Node: getPopularity
// Node: getPercentage
// Node: addChallengeToSolved_WhenNotAddedAndTimesSolvedIsNullOrZero_SetTimesSolvedToOneAndReturnsSolvedDTO
// Node: getChallengesByFilter_ValidParams_FiltersAppliedCorrectly
// Node: válido
// Node: getChallengesByFilter_NoLanguage_FilterAppliedCorrectly
// Node: getChallengesByFilter_InvalidLevel_NoChallengesReturned
// Node: getChallengesByFilter_EmptyTags_NoChallengesReturned
// Node: getRelatedChallenges_NoRelatedChallenges_ReturnsEmptyList
// Node: getRelatedChallenges_LanguageIdEmpty_ShouldNotFilterByLanguage
// Node: getRelatedChallenges_ChallengeWithNullLanguageId_ShouldBeExcluded
// Node: getRelatedChallenges_LevelEmpty_ShouldNotFilterByLevel
// Node: getRelatedChallenges_TagsExistButChallengeHasNoTags_ShouldBeExcluded
// Node: getRelatedChallenges_LessThanThreeRelatedChallenges_ReturnsAll
// Node: getRelatedChallenges_MoreThanThreeRelatedChallenges_ReturnsThreeRandom
// Node: buildChallengeDtoFromDocument
// Node: timesBookmark
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



// Node: shouldReturnLanguageDocumentWhenIdExists
// Node: setLanguageName
// Node: shouldReturnLanguageDocumentWhenLanguageNameExists
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

// Node: getChallengeById_cacheTest
// Node: cache
// Node: atLeastOnce
// Node: call
// Node: getAllChallenges_cacheTest
// Node: testGetChallengeSolutions_cacheTest
// Node: containsExactly
package com.itachallenge.challenge.helper;

import com.itachallenge.challenge.document.*;
import com.itachallenge.challenge.dto.ChallengeDto;
import com.itachallenge.challenge.dto.LanguageDto;
import com.itachallenge.challenge.enums.Topic;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import reactor.core.publisher.Flux;

import java.time.LocalDateTime;
import java.util.*;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.*;


class ChallengeDocumentToDtoConverterTest {

    private DocumentToDtoConverter<ChallengeDocument, ChallengeDto> converter;

    private ChallengeDocument challengeDoc1;

    private ChallengeDocument challengeDoc2;

    private ChallengeDto challengeDto1;

    private ChallengeDto challengeDto2;

    @BeforeEach
    public void setUp() {
        converter = new DocumentToDtoConverter<>();

        UUID challengeRandomId1 = UUID.randomUUID();
        UUID challengeRandomId2 = UUID.randomUUID();
        UUID languageRandomId1 = UUID.randomUUID();
        UUID languageRandomId2 = UUID.randomUUID();
        UUID solutionsRandomId = UUID.randomUUID();
        UUID tagIdRandom = UUID.randomUUID();

        String[] languageNames = new String[]{"name1", "name2"};
        List<UUID> tags = List.of(tagIdRandom);
        String title = "Title";
        String level = "Hard";
        LocalDateTime localDateTime = LocalDateTime.of(2023, 6, 5, 12, 30, 0);
        String creationDate = "2023-06-05";
        String description = "Some detail";
        DetailDocument detail = new DetailDocument(description);

        Integer popularity = 0;
        Float percentage = 0.0f;

        LanguageDocument languageDoc1 = new LanguageDocument(languageRandomId1, languageNames[0], "https://image-default.com/javascript.png");
        LanguageDocument languageDoc2 = new LanguageDocument(languageRandomId2, languageNames[1], "https://image-default.com/python.png");
        LanguageDto languageDto1 = new LanguageDto(languageRandomId1, languageNames[0], "https://image-default.com/javascript.png");
        LanguageDto languageDto2 = new LanguageDto(languageRandomId2, languageNames[1], "https://image-default.com/python.png");

        Topic topic = Topic.DEBUGGING;
        int timesFavorite = 20;
        int timesBookmark = 30;
        int timesSolved = 40;

        challengeDoc1 = new ChallengeDocument(challengeRandomId1, title, level, localDateTime, detail,
                Set.of(languageDoc1, languageDoc2), List.of(solutionsRandomId), topic, timesFavorite, timesBookmark, timesSolved, tags);

        challengeDoc2 = new ChallengeDocument(challengeRandomId2, title, level, localDateTime, detail,
                Set.of(languageDoc1, languageDoc2), List.of(solutionsRandomId), topic, timesFavorite, timesBookmark, timesSolved, tags);

        challengeDto1 = getChallengeDtoMocked(challengeRandomId1, title, level, creationDate, detail,
                Set.of(languageDto1, languageDto2),
                List.of(solutionsRandomId),
                popularity, percentage, tags);

        challengeDto2 = getChallengeDtoMocked(challengeRandomId2, title, level, creationDate, detail,
                Set.of(languageDto1, languageDto2),
                List.of(solutionsRandomId),
                popularity, percentage, tags);
    }

    @Test
    @DisplayName("Conversion from ChallengeDocument to ChallengeDto. Testing 'convertDocumentToDto' method.")
    void testConvertToDto(){
        ChallengeDocument challengeDocumentMocked = challengeDoc1;
        ChallengeDto resultDto = converter.convertDocumentToDto(challengeDocumentMocked, ChallengeDto.class);
        ChallengeDto expectedDto = challengeDto1;

        assertThat(expectedDto).usingRecursiveComparison()
                .ignoringFields("percentage", "popularity")
                .isEqualTo(resultDto);
    }

    @Test
    @DisplayName("Testing Flux conversion. Test convertDocumentFluxToDtoFlux method.")
    void fromFluxDocToFluxDto() {
        ChallengeDocument challengeDoc1 = this.challengeDoc1;
        ChallengeDocument challengeDoc2 = this.challengeDoc2;

        Flux<ChallengeDto> resultDto = converter.convertDocumentFluxToDtoFlux(Flux.just(challengeDoc1, challengeDoc2), ChallengeDto.class);



        assertThat(resultDto.count().block()).isEqualTo(Long.valueOf(2));

        assertThat(resultDto.blockFirst()).usingRecursiveComparison()
                .ignoringFields("percentage", "popularity")
                .isEqualTo(challengeDto1);
        assertThat(resultDto.blockLast()).usingRecursiveComparison()
                .ignoringFields("percentage", "popularity")
                .isEqualTo(challengeDto2);
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
        when(challengeDocMocked.getTopic()).thenReturn(Topic.DEBUGGING);
        when(challengeDocMocked.getTimesFavorite()).thenReturn(20);
        when(challengeDocMocked.getTimesBookmark()).thenReturn(30);
        when(challengeDocMocked.getTimesSolved()).thenReturn(40);
        when(challengeDocMocked.getTags()).thenReturn(tags);
        return challengeDocMocked;
    }
}

// Node: testConvertToDto
// Node: ignoringFields
// Node: fromFluxDocToFluxDto
// Node: blockFirst
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



// Node: testConvertFluxEntityToFluxDto
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



// Node: DocumentToDtoConverter
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



// Node: ChallengeFilterDto
// Node: testSetters
// Node: setOffset
// Node: setLimit
// Node: buildLanguages
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








// Node: copyOf
// Node: popularity
// Node: percentage
