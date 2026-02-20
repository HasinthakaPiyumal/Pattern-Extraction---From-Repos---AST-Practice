// Cluster 6

// Node: getHeader
package com.itachallenge.githubcore.service;

import com.itachallenge.githubcore.document.enums.GithubUserStatus;
import reactor.core.publisher.Mono;

public interface GithubApiService {
    Mono<GithubUserStatus> userExists(String username);
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/github-core/src/main/java/com/itachallenge/githubcore/service/GithubApiService.java:GithubApiService.<init>
// Node: userExists
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

// Node: repos/cloned_ms_repos/ita-challenges-backend/github-core/src/test/java/com/itachallenge/githubcore/service/GithubApiServiceImplTest.java:GithubApiServiceImplTest.<init>
// Node: startServer
// Node: MockWebServer
// Node: start
// Node: shutdownServer
// Node: shutdown
// Node: exists_ShouldReturnTrue_WhenResponseIs200
// Node: enqueue
// Node: MockResponse
// Node: setResponseCode
// Node: setBody
// Node: addHeader
// Node: create
// Node: expectNext
// Node: verifyComplete
// Node: exists_ShouldReturnFalse_WhenResponseIs404
// Node: exists_ShouldReturnFalse_WhenResponseIs500
// Node: expectError
package com.itachallenge.user.service;

import reactor.core.publisher.Mono;

public interface ExternalGithubService {
    Mono<Boolean> userExists(String username);
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/service/ExternalGithubService.java:ExternalGithubService.<init>
// Node: expectNextMatches
// Node: takeRequest
// Node: getRequestUrl
// Node: encodedPath
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


// Node: testUserExistsReturnsTrue
// Node: testUserExistsReturnsFalse
// Node: getRequestData
package com.itachallenge.challenge.repository;


import com.itachallenge.challenge.document.ChallengeDocument;

import com.itachallenge.challenge.enums.Topic;
import org.springframework.data.repository.reactive.ReactiveSortingRepository;
import org.springframework.stereotype.Repository;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import org.springframework.data.mongodb.repository.Query;

import java.awt.print.Pageable;
import java.util.UUID;



@Repository
public interface ChallengeRepository extends ReactiveSortingRepository<ChallengeDocument, UUID> {

    Mono<Boolean> existsByUuid(UUID uuid);
    Mono<ChallengeDocument> findByUuid(UUID uuid);
    Flux<ChallengeDocument> findByLevel(String level);
    @Query(value = "{}")
    Flux<ChallengeDocument> findAllByUuidNotNullExcludingTestingValues();
    Mono<Long> count();
    Mono<Void> deleteByUuid(UUID uuid);
    Mono<ChallengeDocument> save(ChallengeDocument challenge);
    Flux<ChallengeDocument> saveAll(Flux<ChallengeDocument> challengeDocumentFlux);
    @Query(value = "{ 'level' : ?0, 'languages.idLanguage' : ?1 }")
    Flux<ChallengeDocument> findByLevelAndLanguages_IdLanguage(String level, UUID idLanguage);
    @Query(value = "{ 'languages.idLanguage' : ?0 }")
    Flux<ChallengeDocument> findByLanguages_IdLanguage(UUID idLanguage);
    Flux<ChallengeDocument> findByLanguages_LanguageName(String languageName);
    @Query(value = "{ 'challenge_title' : { $regex: ?0, $options: 'i' } }", exists = true)
    Mono<Boolean> existsByChallengeTitle(String title);
    @Query(value = "{ 'challenge_title.ca' : { $regex: ?0, $options: 'i' } }", exists = true)
    Mono<Boolean> existsByChallengeTitleCa(String title);
    Flux<ChallengeDocument> findByTopic(Topic topic);

}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/repository/ChallengeRepository.java:ChallengeRepository.<init>
// Node: findByLevel
// Node: findByLevelAndLanguages_IdLanguage
// Node: findByLanguages_IdLanguage
// Node: findByLanguages_LanguageName
// Node: existsByChallengeTitleCa
// Node: findByTopic
// Node: findByResourceId
// Node: findByContentType
// Node: findByChallengeIdsContaining
// Node: findAll
// Node: updateResourceByUuid
// Node: DeleteResponseDto
// Node: getId
// Node: getTimesBookmark
// Node: BookmarkDto
// Node: FavoriteDto
// Node: setResourceId
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

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/challenge/proxy/HttpProxyTest.java:HttpProxyTest.<init>
// Node: getRequestDataTest
// Node: getPort
// Node: providedUrlNotValidTest
// Node: expectErrorMessage
// Node: available
// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/challenge/proxy/HttpProxyTest.java:HttpProxyTest.clientIsDownTest
// Node: clientIsDownTest
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


// Node: getOneChallenge_ChallengeFound_ReturnsOkResponse
// Node: deleteOneChallenge_success
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

// Node: addFavorite_success_200
// Node: is2xxSuccessful
// Node: removeFavorite_success_200
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


// Node: findAllTagsTest
// Node: expectNextCount
// Node: findByIdLanguageTest
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

// Node: findAllTest
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


// Node: findByResourceIdTest
// Node: findByTopicTest
// Node: thenCancel
// Node: findByContentTypeTest
// Node: deleteByResourceIdTest
// Node: countResourcesTest
// Node: findByNonExistingResourceIdTest
// Node: deleteAllResourcesTest
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

// Node: findAllChallengeByLanguagesAndLevelGetOne
// Node: findByLanguages_idLanguage_test
// Node: findByLanguages_LanguageName_test
// Node: findByLevelFlux_test
// Node: addSolutionToChallengeTest
// Node: addSolutionToSolutionsTest
// Node: findByDetailTopicTest
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

// Node: getValidatedTags_returnsTrue_test
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

// Node: getChallengeById_InvalidId_ErrorThrown
// Node: updateResourceByUuid_InvalidUUID
// Node: getChallengesByTopic_WhenChallengesExist_ReturnsResult
// Node: getTotal
// Node: getChallengesByTopic_WhenNoChallengesExist_ReturnsEmptyResult
// Node: addChallengeToBookmarks_WhenAdded_IncreasesTimesBookmarkAndReturnsFavoriteDTO
// Node: setTimesBookmark
// Node: getTimesBookmarked
// Node: isBookmarked
// Node: addChallengeToBookmarks_WhenAddedAndInitialTimesFavoriteIsNull_IncreasesTimesBookmarkAndReturnsBookmarkDTO
// Node: addChallengeToBookmarks_WhenNotAdded_NotIncreaseTimesBookmarkAndReturnsBookmarkDTO
// Node: addChallengeToBookmarks_WhenNotAddedAndTimesBookmarkIsNullOrZero_SetTimesBookmarkToOneAndReturnsBookmarkDTO
// Node: getRelatedChallenges_InvalidUUID_ThrowsBadUUIDException
// Node: removeChallengeFromBookmarks_WhenRemoved_DecreasesTimesBookmarkedAndReturnsBookmarkDTO
// Node: removeChallengeFromBookmarks_WhenRemovedAndInitialTimesBookmarkedIsNull_SetsTimesBookmarkedToZeroAndReturnsBookmarkDTO
// Node: removeChallengeFromBookmarks_WhenRemovedAndInitialTimesBookmarkedIsZero_SetsTimesBookmarkedToZeroAndReturnsBookmarkDTO
// Node: removeChallengeFromBookmarks_WhenNotRemoved_NotChangeTimesBookmarkedAndReturnsBookmarkDTO
// Node: removeChallengeFromBookmarks_WhenNotRemovedAndTimesBookmarkIsNullOrZero_SetTimesBookmarkedToZeroAndReturnsBookmarkDTO
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



// Node: shouldReturnEmptyWhenIdDoesNotExist
// Node: shouldReturnEmptyWhenLanguageNameDoesNotExist
package com.itachallenge.challenge.service;

import com.itachallenge.common.exception.BadRequestException;
import com.itachallenge.challenge.exception.InternalServerErrorException;
import com.itachallenge.challenge.exception.UserNotFoundException;
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

public class UserServiceImplTest {

    private MockWebServer mockWebServer;
    private UserServiceImpl userService;
    private static final String FAVORITES_URL =
            "/itachallenge/api/v1/userinteraction/favorites/users/%s/favorites/%s";
    private static final String BOOKMARKS_URL =
            "/itachallenge/api/v1/user/users/%s/bookmarks/%s";
    private static final String FAVORITES_TEMPLATE =
            "/itachallenge/api/v1/userinteraction/favorites/users/{userId}/favorites/{challengeId}";
    private static final String BOOKMARKS_TEMPLATE =
            "/itachallenge/api/v1/user/users/{userId}/bookmarks/{challengeId}";
    private static final String SOLVED_URL = "/itachallenge/api/v1/user/users/%s/solved/%s";
    public static final String X_FAVORITE_MESSAGE = "X-Favorite-Message";
    public static final String X_BOOKMARK_MESSAGE = "X-Bookmark-Message";
    public static final String X_SOLVED_MESSAGE = "X-Solved-Message";

    @BeforeEach
    void setUp() throws IOException {
        mockWebServer = new MockWebServer();
        mockWebServer.start();

        userService = new UserServiceImpl(
                WebClient.builder(),
                mockWebServer.url("").toString(),
                FAVORITES_TEMPLATE,
                BOOKMARKS_TEMPLATE
        );
    }

    @AfterEach
    void tearDown() throws IOException {
        mockWebServer.close();
    }

    @Test
    void addChallengeToFavorites_AddedToUser_ReturnsTrue() throws InterruptedException {
        String userId = "someId";
        String challengeId = "anotherId";

        mockWebServer.enqueue(new MockResponse()
                .setBody("true")
                .setResponseCode(201)
                .addHeader("Content-Type", "application/json"));

        Mono<Boolean> result = userService.addChallengeToFavorites(userId, challengeId);

        StepVerifier.create(result)
                .expectNext(true)
                .verifyComplete();

        RecordedRequest request = mockWebServer.takeRequest();
        assertNotNull(request.getRequestUrl());
        assertEquals(
                String.format(FAVORITES_URL, userId, challengeId),
                request.getRequestUrl().encodedPath());
    }

    @Test
    void addChallengeToBookmarks_AddedToUser_ReturnsTrue() throws InterruptedException {
        String userId = "someId";
        String challengeId = "anotherId";

        mockWebServer.enqueue(new MockResponse()
                .setBody("true")
                .setResponseCode(201)
                .addHeader("Content-Type", "application/json"));

        Mono<Boolean> result = userService.addChallengeToBookmarks(userId, challengeId);

        StepVerifier.create(result)
                .expectNext(true)
                .verifyComplete();

        RecordedRequest request = mockWebServer.takeRequest();
        assertNotNull(request.getRequestUrl());
        assertEquals(
                String.format(BOOKMARKS_URL, userId, challengeId),
                request.getRequestUrl().encodedPath());
        assertEquals("POST", request.getMethod());
    }

    @Test
    void addChallengeToFavorites_NotAddedToUser_ReturnsFalse() throws InterruptedException {
        String userId = "someId";
        String challengeId = "anotherId";

        mockWebServer.enqueue(new MockResponse()
                .setBody("false")
                .setResponseCode(200)
                .addHeader("Content-Type", "application/json"));

        Mono<Boolean> result = userService.addChallengeToFavorites(userId, challengeId);

        StepVerifier.create(result)
                .expectNext(false)
                .verifyComplete();

        RecordedRequest request = mockWebServer.takeRequest();
        assertNotNull(request.getRequestUrl());
        assertEquals(
                String.format(FAVORITES_URL, userId, challengeId),
                request.getRequestUrl().encodedPath());
    }

    @Test
    void addChallengeToBookmarks_NotAddedToUser_ReturnsFalse() throws InterruptedException {
        String userId = "someId";
        String challengeId = "anotherId";

        mockWebServer.enqueue(new MockResponse()
                .setBody("false")
                .setResponseCode(200)
                .addHeader("Content-Type", "application/json"));

        Mono<Boolean> result = userService.addChallengeToBookmarks(userId, challengeId);

        StepVerifier.create(result)
                .expectNext(false)
                .verifyComplete();

        RecordedRequest request = mockWebServer.takeRequest();
        assertNotNull(request.getRequestUrl());
        assertEquals(
                String.format(BOOKMARKS_URL, userId, challengeId),
                request.getRequestUrl().encodedPath());
        assertEquals("POST", request.getMethod());
    }

    @Test
    void addChallengeToFavorites_BadRequest_ReturnsError() throws InterruptedException {
        String userId = "someId";
        String challengeId = "anotherId";
        String someErrorMessage = "Some error message";

        mockWebServer.enqueue(new MockResponse()
                .setBody("false")
                .setResponseCode(400)
                .addHeader(X_FAVORITE_MESSAGE, someErrorMessage)
                .addHeader("Content-Type", "application/json"));

        Mono<Boolean> result = userService.addChallengeToFavorites(userId, challengeId);

        StepVerifier.create(result)
                .expectErrorSatisfies(throwable -> {
                    assertInstanceOf(BadRequestException.class, throwable);
                    assertTrue(throwable.getMessage().contains(someErrorMessage));
                })
                .verify();

        RecordedRequest request = mockWebServer.takeRequest();
        assertNotNull(request.getRequestUrl());
        assertEquals(
                String.format(FAVORITES_URL, userId, challengeId),
                request.getRequestUrl().encodedPath());
    }

    @Test
    void addChallengeToBookmarks_BadRequest_ReturnsError() throws InterruptedException {
        String userId = "someId";
        String challengeId = "anotherId";
        String someErrorMessage = "Some error message";

        mockWebServer.enqueue(new MockResponse()
                .setBody("false")
                .setResponseCode(400)
                .addHeader(X_BOOKMARK_MESSAGE, someErrorMessage)
                .addHeader("Content-Type", "application/json"));

        Mono<Boolean> result = userService.addChallengeToBookmarks(userId, challengeId);

        StepVerifier.create(result)
                .expectErrorSatisfies(throwable -> {
                    assertInstanceOf(BadRequestException.class, throwable);
                    assertTrue(throwable.getMessage().contains(someErrorMessage));
                })
                .verify();

        RecordedRequest request = mockWebServer.takeRequest();
        assertNotNull(request.getRequestUrl());
        assertEquals(
                String.format(BOOKMARKS_URL, userId, challengeId),
                request.getRequestUrl().encodedPath());
        assertEquals("POST", request.getMethod());
    }

    @Test
    void addChallengeToFavorites_UserNotFound_ReturnsError() throws InterruptedException {
        String userId = "someId";
        String challengeId = "anotherId";

        mockWebServer.enqueue(new MockResponse()
                .setBody("false")
                .setResponseCode(404)
                .addHeader("Content-Type", "application/json"));

        Mono<Boolean> result = userService.addChallengeToFavorites(userId, challengeId);

        StepVerifier.create(result)
                .expectErrorSatisfies(throwable -> {
                    assertInstanceOf(UserNotFoundException.class, throwable);
                    assertTrue(throwable.getMessage().contains("User not found"));
                })
                .verify();

        RecordedRequest request = mockWebServer.takeRequest();
        assertNotNull(request.getRequestUrl());
        assertEquals(
                String.format(FAVORITES_URL, userId, challengeId),
                request.getRequestUrl().encodedPath());
    }

    @Test
    void addChallengeToBookmarks_UserNotFound_ReturnsError() throws InterruptedException {
        String userId = "someId";
        String challengeId = "anotherId";

        mockWebServer.enqueue(new MockResponse()
                .setBody("false")
                .setResponseCode(404)
                .addHeader("Content-Type", "application/json"));

        Mono<Boolean> result = userService.addChallengeToBookmarks(userId, challengeId);

        StepVerifier.create(result)
                .expectErrorSatisfies(throwable -> {
                    assertInstanceOf(UserNotFoundException.class, throwable);
                    assertTrue(throwable.getMessage().contains("User not found"));
                })
                .verify();

        RecordedRequest request = mockWebServer.takeRequest();
        assertNotNull(request.getRequestUrl());
        assertEquals(
                String.format(BOOKMARKS_URL, userId, challengeId),
                request.getRequestUrl().encodedPath());
        assertEquals("POST", request.getMethod());
    }

    @Test
    void addChallengeToFavorites_500_ReturnsError() throws InterruptedException {
        String userId = "someId";
        String challengeId = "anotherId";
        String someErrorMessage = "Some error message";

        mockWebServer.enqueue(new MockResponse()
                .setBody("false")
                .setResponseCode(500)
                .addHeader(X_FAVORITE_MESSAGE, someErrorMessage)
                .addHeader("Content-Type", "application/json"));

        Mono<Boolean> result = userService.addChallengeToFavorites(userId, challengeId);

        StepVerifier.create(result)
                .expectErrorSatisfies(throwable -> {
                    assertInstanceOf(InternalServerErrorException.class, throwable);
                    assertTrue(throwable.getMessage().contains(throwable.getMessage()));
                })
                .verify();

        RecordedRequest request = mockWebServer.takeRequest();
        assertNotNull(request.getRequestUrl());
        assertEquals(
                String.format(FAVORITES_URL, userId, challengeId),
                request.getRequestUrl().encodedPath());
    }

    @Test
    void addChallengeToBookmarks_500_ReturnsError() throws InterruptedException {
        String userId = "someId";
        String challengeId = "anotherId";
        String someErrorMessage = "Some error message";

        mockWebServer.enqueue(new MockResponse()
                .setBody("false")
                .setResponseCode(500)
                .addHeader(X_BOOKMARK_MESSAGE, someErrorMessage)
                .addHeader("Content-Type", "application/json"));

        Mono<Boolean> result = userService.addChallengeToBookmarks(userId, challengeId);

        StepVerifier.create(result)
                .expectErrorSatisfies(throwable -> {
                    assertInstanceOf(InternalServerErrorException.class, throwable);
                    assertTrue(throwable.getMessage().contains(someErrorMessage));
                })
                .verify();

        RecordedRequest request = mockWebServer.takeRequest();
        assertNotNull(request.getRequestUrl());
        assertEquals(
                String.format(BOOKMARKS_URL, userId, challengeId),
                request.getRequestUrl().encodedPath());
        assertEquals("POST", request.getMethod());
    }

    @Test
    void removeChallengeFromFavorites_DeletedFromUser_ReturnsTrue() throws InterruptedException {
        String userId = "someId";
        String challengeId = "anotherId";

        mockWebServer.enqueue(new MockResponse()
                .setBody("true")
                .setResponseCode(201)
                .addHeader("Content-Type", "application/json"));

        Mono<Boolean> result = userService.removeChallengeFromFavorites(userId, challengeId);

        StepVerifier.create(result)
                .expectNext(true)
                .verifyComplete();

        RecordedRequest request = mockWebServer.takeRequest();
        assertNotNull(request.getRequestUrl());
        assertEquals(
                String.format(FAVORITES_URL, userId, challengeId),
                request.getRequestUrl().encodedPath());
        assertEquals("DELETE", request.getMethod());
    }

    @Test
    void removeChallengeFromFavorites_NotDeletedFromUser_ReturnsFalse() throws InterruptedException {
        String userId = "someId";
        String challengeId = "anotherId";

        mockWebServer.enqueue(new MockResponse()
                .setBody("false")
                .setResponseCode(200)
                .addHeader("Content-Type", "application/json"));

        Mono<Boolean> result = userService.removeChallengeFromFavorites(userId, challengeId);

        StepVerifier.create(result)
                .expectNext(false)
                .verifyComplete();

        RecordedRequest request = mockWebServer.takeRequest();
        assertNotNull(request.getRequestUrl());
        assertEquals(
                String.format(FAVORITES_URL, userId, challengeId),
                request.getRequestUrl().encodedPath());
        assertEquals("DELETE", request.getMethod());
    }

    @Test
    void removeChallengeFromFavorites_BadRequest_ReturnsError() throws InterruptedException {
        String userId = "someId";
        String challengeId = "anotherId";
        String someErrorMessage = "Some error message";

        mockWebServer.enqueue(new MockResponse()
                .setBody("false")
                .setResponseCode(400)
                .addHeader(X_FAVORITE_MESSAGE, someErrorMessage)
                .addHeader("Content-Type", "application/json"));

        Mono<Boolean> result = userService.removeChallengeFromFavorites(userId, challengeId);

        StepVerifier.create(result)
                .expectErrorSatisfies(throwable -> {
                    assertInstanceOf(BadRequestException.class, throwable);
                    assertTrue(throwable.getMessage().contains(someErrorMessage));
                })
                .verify();

        RecordedRequest request = mockWebServer.takeRequest();
        assertNotNull(request.getRequestUrl());
        assertEquals(
                String.format(FAVORITES_URL, userId, challengeId),
                request.getRequestUrl().encodedPath());
        assertEquals("DELETE", request.getMethod());
    }

    @Test
    void removeChallengeFromFavorites_UserNotFound_ReturnsError() throws InterruptedException {
        String userId = "someId";
        String challengeId = "anotherId";

        mockWebServer.enqueue(new MockResponse()
                .setBody("false")
                .setResponseCode(404)
                .addHeader("Content-Type", "application/json"));

        Mono<Boolean> result = userService.removeChallengeFromFavorites(userId, challengeId);

        StepVerifier.create(result)
                .expectErrorSatisfies(throwable -> {
                    assertInstanceOf(UserNotFoundException.class, throwable);
                    assertTrue(throwable.getMessage().contains("User not found"));
                })
                .verify();

        RecordedRequest request = mockWebServer.takeRequest();
        assertNotNull(request.getRequestUrl());
        assertEquals(
                String.format(FAVORITES_URL, userId, challengeId),
                request.getRequestUrl().encodedPath());
        assertEquals("DELETE", request.getMethod());
    }

    @Test
    void removeChallengeFromFavorites_500_ReturnsError() throws InterruptedException {
        String userId = "someId";
        String challengeId = "anotherId";
        String someErrorMessage = "Some error message";

        mockWebServer.enqueue(new MockResponse()
                .setBody("false")
                .setResponseCode(500)
                .addHeader(X_FAVORITE_MESSAGE, someErrorMessage)
                .addHeader("Content-Type", "application/json"));

        Mono<Boolean> result = userService.removeChallengeFromFavorites(userId, challengeId);

        StepVerifier.create(result)
                .expectErrorSatisfies(throwable -> {
                    assertInstanceOf(InternalServerErrorException.class, throwable);
                    assertTrue(throwable.getMessage().contains(throwable.getMessage()));
                })
                .verify();

        RecordedRequest request = mockWebServer.takeRequest();
        assertNotNull(request.getRequestUrl());
        assertEquals(
                String.format(FAVORITES_URL, userId, challengeId),
                request.getRequestUrl().encodedPath());
        assertEquals("DELETE", request.getMethod());
    }

    @Test
    void removeChallengeFromBookmarks_DeletedFromUser_ReturnsTrue() throws InterruptedException {
        String userId = "someId";
        String challengeId = "anotherId";

        mockWebServer.enqueue(new MockResponse()
                .setBody("true")
                .setResponseCode(201)
                .addHeader("Content-Type", "application/json"));

        Mono<Boolean> result = userService.removeChallengeFromBookmarks(userId, challengeId);

        StepVerifier.create(result)
                .expectNext(true)
                .verifyComplete();

        RecordedRequest request = mockWebServer.takeRequest();
        assertNotNull(request.getRequestUrl());
        assertEquals(
                String.format(BOOKMARKS_URL, userId, challengeId),
                request.getRequestUrl().encodedPath());
        assertEquals("DELETE", request.getMethod());
    }

    @Test
    void removeChallengeFromBookmarks_NotDeletedFromUser_ReturnsFalse() throws InterruptedException {
        String userId = "someId";
        String challengeId = "anotherId";

        mockWebServer.enqueue(new MockResponse()
                .setBody("false")
                .setResponseCode(200)
                .addHeader("Content-Type", "application/json"));

        Mono<Boolean> result = userService.removeChallengeFromBookmarks(userId, challengeId);

        StepVerifier.create(result)
                .expectNext(false)
                .verifyComplete();

        RecordedRequest request = mockWebServer.takeRequest();
        assertNotNull(request.getRequestUrl());
        assertEquals(
                String.format(BOOKMARKS_URL, userId, challengeId),
                request.getRequestUrl().encodedPath());
        assertEquals("DELETE", request.getMethod());
    }

    @Test
    void removeChallengeFromBookmarks_BadRequest_ReturnsError() throws InterruptedException {
        String userId = "someId";
        String challengeId = "anotherId";
        String someErrorMessage = "Some error message";

        mockWebServer.enqueue(new MockResponse()
                .setBody("false")
                .setResponseCode(400)
                .addHeader(X_BOOKMARK_MESSAGE, someErrorMessage)
                .addHeader("Content-Type", "application/json"));

        Mono<Boolean> result = userService.removeChallengeFromBookmarks(userId, challengeId);

        StepVerifier.create(result)
                .expectErrorSatisfies(throwable -> {
                    assertInstanceOf(BadRequestException.class, throwable);
                    assertTrue(throwable.getMessage().contains(someErrorMessage));
                })
                .verify();

        RecordedRequest request = mockWebServer.takeRequest();
        assertNotNull(request.getRequestUrl());
        assertEquals(
                String.format(BOOKMARKS_URL, userId, challengeId),
                request.getRequestUrl().encodedPath());
        assertEquals("DELETE", request.getMethod());
    }

    @Test
    void removeChallengeFromBookmarks_UserNotFound_ReturnsError() throws InterruptedException {
        String userId = "someId";
        String challengeId = "anotherId";

        mockWebServer.enqueue(new MockResponse()
                .setBody("false")
                .setResponseCode(404)
                .addHeader("Content-Type", "application/json"));

        Mono<Boolean> result = userService.removeChallengeFromBookmarks(userId, challengeId);

        StepVerifier.create(result)
                .expectErrorSatisfies(throwable -> {
                    assertInstanceOf(UserNotFoundException.class, throwable);
                    assertTrue(throwable.getMessage().contains("User not found"));
                })
                .verify();

        RecordedRequest request = mockWebServer.takeRequest();
        assertNotNull(request.getRequestUrl());
        assertEquals(
                String.format(BOOKMARKS_URL, userId, challengeId),
                request.getRequestUrl().encodedPath());
        assertEquals("DELETE", request.getMethod());
    }

    @Test
    void removeChallengeFromBookmarks_500_ReturnsError() throws InterruptedException {
        String userId = "someId";
        String challengeId = "anotherId";
        String someErrorMessage = "Some error message";

        mockWebServer.enqueue(new MockResponse()
                .setBody("false")
                .setResponseCode(500)
                .addHeader(X_BOOKMARK_MESSAGE, someErrorMessage)
                .addHeader("Content-Type", "application/json"));

        Mono<Boolean> result = userService.removeChallengeFromBookmarks(userId, challengeId);

        StepVerifier.create(result)
                .expectErrorSatisfies(throwable -> {
                    assertInstanceOf(InternalServerErrorException.class, throwable);
                    assertTrue(throwable.getMessage().contains(throwable.getMessage()));
                })
                .verify();

        RecordedRequest request = mockWebServer.takeRequest();
        assertNotNull(request.getRequestUrl());
        assertEquals(
                String.format(BOOKMARKS_URL, userId, challengeId),
                request.getRequestUrl().encodedPath());
        assertEquals("DELETE", request.getMethod());
    }

}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/challenge/service/UserServiceImplTest.java:UserServiceImplTest.<init>
// Node: addChallengeToFavorites_AddedToUser_ReturnsTrue
// Node: addChallengeToBookmarks_AddedToUser_ReturnsTrue
// Node: addChallengeToFavorites_NotAddedToUser_ReturnsFalse
// Node: addChallengeToBookmarks_NotAddedToUser_ReturnsFalse
// Node: addChallengeToFavorites_BadRequest_ReturnsError
// Node: addChallengeToBookmarks_BadRequest_ReturnsError
// Node: addChallengeToFavorites_UserNotFound_ReturnsError
// Node: addChallengeToBookmarks_UserNotFound_ReturnsError
// Node: addChallengeToFavorites_500_ReturnsError
// Node: addChallengeToBookmarks_500_ReturnsError
// Node: removeChallengeFromFavorites_DeletedFromUser_ReturnsTrue
// Node: removeChallengeFromFavorites_NotDeletedFromUser_ReturnsFalse
// Node: removeChallengeFromFavorites_BadRequest_ReturnsError
// Node: removeChallengeFromFavorites_UserNotFound_ReturnsError
// Node: removeChallengeFromFavorites_500_ReturnsError
// Node: removeChallengeFromBookmarks_DeletedFromUser_ReturnsTrue
// Node: removeChallengeFromBookmarks_NotDeletedFromUser_ReturnsFalse
// Node: removeChallengeFromBookmarks_BadRequest_ReturnsError
// Node: removeChallengeFromBookmarks_UserNotFound_ReturnsError
// Node: removeChallengeFromBookmarks_500_ReturnsError
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


// Node: createResource_WithNullResourceDto_ShouldThrowError
// Node: getResourcesByChallengeId_WhenResourcesExist_ReturnsFluxOfResources
// Node: ResourceDto
// Node: getResourcesByChallengeId_WhenNoResourcesExist_ReturnsEmptyFlux
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


// Node: testAllArgsConstructorAndGetters
// Node: setBookmarked
// Node: setTimesBookmarked
// Node: testNoArgsConstructorDefaultValues
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


// Node: testMessageAndID
// Node: User
package com.itachallenge.auth.service;


import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import okhttp3.mockwebserver.RecordedRequest;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

import java.io.IOException;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;

class AuthServiceTest {

    private MockWebServer mockWebServer;
    private AuthService authService;

    @BeforeEach
    void setUp() throws IOException {
        mockWebServer = new MockWebServer();
        mockWebServer.start();

        String baseUrl = mockWebServer.url("").toString();
        String githubTokenUri = baseUrl + "login/oauth/access_token";
        String githubUserInfoUri = baseUrl + "user";

        authService = new AuthService(
                WebClient.builder(),
                githubTokenUri,
                githubUserInfoUri,
                "test-client-id",
                "test-client-secret");
    }

    @AfterEach
    void tearDown() throws IOException {
        mockWebServer.shutdown();
    }

    @Test
    void exchangeCodeForToken_Successful() throws InterruptedException {
        String code = "auth-code";
        String accessToken = "github-access-token";
        String mockResponse = "{\"access_token\": \"" + accessToken + "\"}";

        mockWebServer.enqueue(new MockResponse()
                .setBody(mockResponse)
                .setResponseCode(200)
                .addHeader("Content-Type", "application/json"));

        Mono<String> result = authService.exchangeCodeForToken(code);

        StepVerifier.create(result)
                .expectNext(accessToken)
                .verifyComplete();

        RecordedRequest request = mockWebServer.takeRequest();
        assertEquals("/login/oauth/access_token", request.getRequestUrl().encodedPath());
        assertEquals("application/json", request.getHeader("Accept"));
    }

    @Test
    void exchangeCodeForToken_InvalidCode_ReturnsError() {
        String code = "invalid-code";
        String mockResponse = "{\"error\": \"bad_verification_code\"}";

        mockWebServer.enqueue(new MockResponse()
                .setBody(mockResponse)
                .setResponseCode(400) // Simulate GitHub rejecting the code
                .addHeader("Content-Type", "application/json"));

        Mono<String> result = authService.exchangeCodeForToken(code);

        StepVerifier.create(result)
                .expectError(WebClientResponseException.BadRequest.class)
                .verify();
    }

    @Test
    void exchangeCodeForToken_NetworkFailure_ReturnsError() {
        String code = "auth-code";

        mockWebServer.enqueue(new MockResponse()
                .setResponseCode(500));

        Mono<String> result = authService.exchangeCodeForToken(code);

        StepVerifier.create(result)
                .expectError(WebClientResponseException.class)
                .verify();
    }

    @Test
    void validateTokenWithGithub_ValidToken_ReturnsUsername() throws Exception {
        String validToken = "valid-token";
        String githubUsername = "octocat";
        String mockResponse = "{\"login\": \"" + githubUsername + "\"}";

        mockWebServer.enqueue(new MockResponse()
                .setBody(mockResponse)
                .setResponseCode(200)
                .addHeader("Content-Type", "application/json"));

        Mono<Map<String, Object>> result = authService.validateTokenWithGithub(validToken);

        StepVerifier.create(result)
                .assertNext(response -> {
                    assertEquals(true, response.get("isValid"));
                    assertEquals(githubUsername, response.get("username"));
                })
                .verifyComplete();

        RecordedRequest request = mockWebServer.takeRequest();
        assertEquals("/user", request.getRequestUrl().encodedPath());
        assertEquals("token " + validToken, request.getHeader("Authorization"));
    }

    @Test
    void validateTokenWithGithub_ExpiredToken_ReturnsInvalid() {
        String expiredToken = "expired-token";
        String mockResponse = "{\"message\": \"Bad credentials\"}";

        mockWebServer.enqueue(new MockResponse()
                .setBody(mockResponse)
                .setResponseCode(401)
                .addHeader("Content-Type", "application/json"));

        Mono<Map<String, Object>> result = authService.validateTokenWithGithub(expiredToken);

        StepVerifier.create(result)
                .assertNext(response -> assertEquals(false, response.get("isValid")))
                .verifyComplete();
    }

    @Test
    void validateTokenWithGithub_UnexpectedResponse_ReturnsError() {
        String token = "valid-token";
        String mockResponse = "{\"unexpected_key\": \"unexpected_value\"}";

        mockWebServer.enqueue(new MockResponse()
                .setBody(mockResponse)
                .setResponseCode(200)
                .addHeader("Content-Type", "application/json"));

        Mono<Map<String, Object>> result = authService.validateTokenWithGithub(token);

        StepVerifier.create(result)
                .assertNext(response -> assertEquals(false, response.get("isValid")))
                .verifyComplete();
    }

}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-auth/src/test/java/com/itachallenge/auth/service/AuthServiceTest.java:AuthServiceTest.<init>
// Node: exchangeCodeForToken_Successful
// Node: exchangeCodeForToken_InvalidCode_ReturnsError
// Node: exchangeCodeForToken_NetworkFailure_ReturnsError
// Node: validateTokenWithGithub_ValidToken_ReturnsUsername
// Node: validateTokenWithGithub_ExpiredToken_ReturnsInvalid
// Node: validateTokenWithGithub_UnexpectedResponse_ReturnsError
package com.itachallenge.auth.service;


import com.itachallenge.auth.dto.User;
import com.itachallenge.auth.exception.CustomBadRequestException;
import com.itachallenge.auth.exception.CustomInternalServerErrorException;
import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import okhttp3.mockwebserver.RecordedRequest;
import org.junit.jupiter.api.AfterEach;
import static org.junit.jupiter.api.Assertions.*;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.web.reactive.function.client.WebClient;
import org.testcontainers.shaded.com.fasterxml.jackson.core.JsonProcessingException;
import org.testcontainers.shaded.com.fasterxml.jackson.databind.ObjectMapper;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

import java.io.IOException;

class UserServiceTest {

    private MockWebServer mockWebServer;
    private UserService userService;

    @BeforeEach
    void setUp() throws IOException {
        mockWebServer = new MockWebServer();
        mockWebServer.start();

        String baseUrl = mockWebServer.url("").toString();
        String userServiceUrl = baseUrl;

        userService = new UserService(
                WebClient.builder(),
                userServiceUrl);
    }

    @AfterEach
    void tearDown() throws IOException {
        mockWebServer.shutdown();
    }

    @Test
    void fetchUserData_UserExists_ReturnsUser() throws InterruptedException, JsonProcessingException {
        String githubUsername = "octocat";
        User expectedUser = new User("1234", githubUsername, "ADMIN");

        ObjectMapper objectMapper = new ObjectMapper();
        mockWebServer.enqueue(new MockResponse()
                .setBody(objectMapper.writeValueAsString(expectedUser))
                .setResponseCode(200)
                .addHeader("Content-Type", "application/json"));

        Mono<User> result = userService.fetchUserData(githubUsername);

        StepVerifier.create(result)
                .expectNext(expectedUser)
                .verifyComplete();

        RecordedRequest request = mockWebServer.takeRequest();
        assertEquals("/itachallenge/api/v1/user/users/" + githubUsername, request.getRequestUrl().encodedPath());
    }

    @Test
    void fetchUserData_NotFound_ReturnsEmptyMono() throws InterruptedException {
        String githubUsername = "octocat";

        mockWebServer.enqueue(new MockResponse()
                .setResponseCode(404)
                .addHeader("Content-Type", "application/json"));

        Mono<User> result = userService.fetchUserData(githubUsername);

        StepVerifier.create(result)
                .expectNextCount(0)
                .verifyComplete();

        RecordedRequest request = mockWebServer.takeRequest();
        assertEquals("/itachallenge/api/v1/user/users/" + githubUsername, request.getRequestUrl().encodedPath());
    }

    @Test
    void fetchUserData_BadRequest_ThrowsCustomBadRequestException() throws InterruptedException {
        String githubUsername = "octocat";

        mockWebServer.enqueue(new MockResponse()
                .setResponseCode(400)
                .addHeader("Content-Type", "application/json"));

        Mono<User> result = userService.fetchUserData(githubUsername);

        StepVerifier.create(result)
                .expectError(CustomBadRequestException.class)
                .verify();

        RecordedRequest request = mockWebServer.takeRequest();
        assertEquals("/itachallenge/api/v1/user/users/" + githubUsername, request.getRequestUrl().encodedPath());
    }

    @Test
    void fetchUserData_500_ThrowsInternalServerErrorException() throws InterruptedException {
        String githubUsername = "octocat";

        mockWebServer.enqueue(new MockResponse()
                .setResponseCode(500)
                .addHeader("Content-Type", "application/json"));

        Mono<User> result = userService.fetchUserData(githubUsername);

        StepVerifier.create(result)
                .expectError(CustomInternalServerErrorException.class)
                .verify();

        RecordedRequest request = mockWebServer.takeRequest();
        assertEquals("/itachallenge/api/v1/user/users/" + githubUsername, request.getRequestUrl().encodedPath());
    }

    @Test
    void callUserTest_Ok_ReturnsSalute() throws InterruptedException {
        String expectedResponse = "Hello from User Micro-Service";

        mockWebServer.enqueue(new MockResponse()
                .setResponseCode(200)
                .setBody(expectedResponse)
                .addHeader("Content-Type", "application/json"));

        Mono<String> result = userService.callUserTest();

        StepVerifier.create(result)
                .expectNext(expectedResponse)
                .verifyComplete();

        RecordedRequest request = mockWebServer.takeRequest();
        assertEquals("/itachallenge/api/v1/user/test", request.getRequestUrl().encodedPath());
    }

    @Test
    void callUserTest_Error_ReturnsErrorMessage() throws InterruptedException {
        mockWebServer.enqueue(new MockResponse()
                .setResponseCode(500)
                .addHeader("Content-Type", "application/json"));

        Mono<String> result = userService.callUserTest();

        StepVerifier.create(result)
                .expectNext("Error calling User microservice")
                .verifyComplete();

        RecordedRequest request = mockWebServer.takeRequest();
        assertEquals("/itachallenge/api/v1/user/test", request.getRequestUrl().encodedPath());
    }

}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-auth/src/test/java/com/itachallenge/auth/service/UserServiceTest.java:UserServiceTest.<init>
// Node: fetchUserData_UserExists_ReturnsUser
// Node: fetchUserData_NotFound_ReturnsEmptyMono
// Node: fetchUserData_BadRequest_ThrowsCustomBadRequestException
// Node: fetchUserData_500_ThrowsInternalServerErrorException
// Node: callUserTest_Ok_ReturnsSalute
// Node: callUserTest_Error_ReturnsErrorMessage
