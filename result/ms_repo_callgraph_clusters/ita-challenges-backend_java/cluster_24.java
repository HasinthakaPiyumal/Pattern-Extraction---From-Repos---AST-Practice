// Cluster 24

package com.itachallenge.errorcore.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

@JsonInclude(JsonInclude.Include.NON_EMPTY)
@Builder
@AllArgsConstructor
@Getter
public class FieldErrorDto {
    private final String objectName;
    private final String field;
    private final String message;
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/error-response-core/src/main/java/com/itachallenge/errorcore/dto/FieldErrorDto.java:FieldErrorDto.<init>
// Node: JsonInclude
package com.itachallenge.errorcore.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

import java.time.Instant;
import java.util.List;

@JsonInclude(JsonInclude.Include.NON_EMPTY)
@AllArgsConstructor
@Getter
@Builder
public class APIErrorResponse {
    @Builder.Default
    private final Instant timestamp = Instant.now();
    private final int status;
    private final String error;
    private final String message;
    private final String path;
    private final List<FieldErrorDto> errors;
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/error-response-core/src/main/java/com/itachallenge/errorcore/dto/APIErrorResponse.java:APIErrorResponse.<init>
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


// Node: acceptTestDto
// Node: NotNull
package com.itachallenge.user.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.itachallenge.user.annotations.GenericUUIDValid;
import com.itachallenge.user.document.enums.SolutionAction;
import jakarta.validation.constraints.NotNull;
import lombok.*;

import org.springframework.stereotype.Component;
@Component
@AllArgsConstructor
@NoArgsConstructor
@Builder
@Getter
@Setter
public class UserSolutionRequestDto {

    @JsonProperty(value ="uuid_user")
    @GenericUUIDValid(message = "Invalid UUID")
    private String userId;

    @JsonProperty(value ="uuid_challenge")
    @GenericUUIDValid(message = "Invalid UUID")
    private String challengeId;

    @JsonProperty(value ="uuid_language")
    @GenericUUIDValid(message = "Invalid UUID")
    private String languageId;

    @NotNull(message = "Action cannot be null")
    @JsonProperty(value ="action")
    private SolutionAction action;

    @JsonProperty(value ="solution_text")
    private String solutionText;

}




// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/dto/UserSolutionRequestDto.java:UserSolutionRequestDto.<init>
// Node: JsonProperty
// Node: GenericUUIDValid
package com.itachallenge.user.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.*;
import org.springframework.stereotype.Component;

@Component
@AllArgsConstructor
@NoArgsConstructor
@Builder
@Getter
@Setter
public class SubmitSolutionResponseDto {

    @JsonProperty("solution_text")
    private String solutionText;

    @JsonProperty("isSolved")
    private Boolean isSolved;

    @JsonProperty("timesSolved")
    private Integer timesSolved;

    @JsonProperty("status")
    private String status;
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/dto/SubmitSolutionResponseDto.java:SubmitSolutionResponseDto.<init>
package com.itachallenge.user.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.*;

@AllArgsConstructor
@NoArgsConstructor
@Builder
@Getter
@Setter
public class AdminCreateUserResponseDto {

    @JsonProperty(value ="uuid_user")
    private String userId;

    @JsonProperty("username")
    private String username;

    @JsonProperty("role")
    private String role;

}

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/dto/AdminCreateUserResponseDto.java:AdminCreateUserResponseDto.<init>
package com.itachallenge.user.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.*;
import org.springframework.stereotype.Component;

@Component
@AllArgsConstructor
@NoArgsConstructor
@Builder
@Getter
@Setter
public class UserSolutionResponseDto {

    @JsonProperty(value ="uuid_user")
    private String userId;

    @JsonProperty(value ="uuid_challenge")
    private String challengeId;

    @JsonProperty(value ="uuid_language")
    private String languageId;

    @JsonProperty(value ="solution_text")
    private String solutionText;

    @JsonProperty("status")
    private String status;
}



// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/dto/UserSolutionResponseDto.java:UserSolutionResponseDto.<init>
package com.itachallenge.user.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.Instant;

@AllArgsConstructor
@NoArgsConstructor
@Getter
@Setter
public class APIErrorResponse {

    @JsonProperty("error")
    String error;

    @JsonProperty("message")
    String message;

    @JsonProperty("timestamp")
    Instant timestamp;

}



// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/dto/APIErrorResponse.java:APIErrorResponse.<init>
package com.itachallenge.user.dto.userinteraction.bookmark;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.*;

import java.time.LocalDateTime;
import java.util.UUID;


@Builder
@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
public class BookmarkResponseDto {

    @JsonProperty(value = "uuid_bookmark")
    private UUID uuid;

    @JsonProperty(value = "user_id")
    private UUID userId;

    @JsonProperty(value = "challenge_id")
    private UUID challengeId;

    @JsonProperty(value = "created_at")
    private LocalDateTime createdAt;
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/dto/userinteraction/bookmark/BookmarkResponseDto.java:BookmarkResponseDto.<init>
package com.itachallenge.user.dto.userinteraction.favorite;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.*;

import java.time.LocalDateTime;
import java.util.UUID;

@Builder
@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
public class FavoriteResponseDto {

    @JsonProperty(value = "uuid_favorite")
    private UUID uuid;

    @JsonProperty(value = "user_id")
    private UUID userId;

    @JsonProperty(value = "challenge_id")
    private UUID challengeId;

    @JsonProperty(value = "created_at")
    private LocalDateTime createdAt;
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/dto/userinteraction/favorite/FavoriteResponseDto.java:FavoriteResponseDto.<init>
package com.itachallenge.common.exception.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.Builder;
import lombok.Getter;

import java.util.Map;

@Getter
@Builder
public class ErrorResponseDto {
    private String errorCode;
    private String message;
    private String timestamp;
    private String path;

    @JsonInclude(JsonInclude.Include.NON_NULL)
    private Map<String, Object> details;
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/common/exception/dto/ErrorResponseDto.java:ErrorResponseDto.<init>
// Node: ValidGenericPattern
package com.itachallenge.challenge.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.itachallenge.challenge.annotations.ValidUUID;
import jakarta.validation.constraints.NotEmpty;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.UUID;

@AllArgsConstructor
@NoArgsConstructor
@Getter
@Setter
public class SolutionDto {
    private static final String UUID_PATTERN = "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$";
    private static final String STRING_PATTERN = "^.{1,500}$";  //max 500 characters    @Id

    @JsonProperty(value = "id_solution", index = 0)
    private UUID uuid;

    //@ValidGenericPattern(pattern = STRING_PATTERN, message = "Solution text cannot be empty")
    @NotEmpty(message = "{solution.text.notEmpty}")
    @JsonProperty(value = "solution_text", index = 1)
    private String solutionText;

    @ValidUUID(message = "{solution.languageId.invalid}")
    @JsonProperty(value = "uuid_language", index = 2)
    private UUID idLanguage;

    @ValidUUID(message = "{solution.challengeId.invalid}")
    @JsonProperty(value = "uuid_challenge", index = 3)
    private UUID idChallenge;

    //constructor for testing with uuid, solutionText and idLanguage
    public SolutionDto(UUID uuid, String solutionText, UUID idLanguage) {
        this.uuid = uuid;
        this.solutionText = solutionText;
        this.idLanguage = idLanguage;
    }

}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/dto/SolutionDto.java:SolutionDto.<init>
// Node: NotEmpty
// Node: ValidUUID
package com.itachallenge.challenge.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.itachallenge.challenge.document.DetailDocument;
import com.itachallenge.challenge.enums.Topic;
import lombok.*;
import org.springframework.stereotype.Component;

import java.util.*;

@Component
@JsonInclude(JsonInclude.Include.NON_EMPTY)
@AllArgsConstructor(access = AccessLevel.PRIVATE)
@NoArgsConstructor
@Builder
@Getter
@Setter
public class ChallengeDto {

    @JsonProperty(value = "id_challenge", index = 0)
    private UUID challengeId;

    @JsonProperty(value = "challenge_title", index = 1)
    private String title;

    @JsonProperty(index = 2)
    private String level;

    /**
     * Este atributo es String solamente en el DTO.
     * En el document, creationDate es de tipo LocalDateTime.
     * En la clase converter, hay un método privado que convierte y formatea
     * los datos de LocalDateTime a String
     * al formato requerido en el .json
     */
    @JsonProperty(value = "creation_date", index = 3)
    private String creationDate;

    @JsonProperty(value = "detail", index = 4)
    private DetailDocument detail;

    @JsonProperty(index = 5)
    private Integer popularity;

    @JsonProperty(index = 6)
    private Float percentage;

    @JsonProperty(index = 7)
    private Set<LanguageDto> languages;

    @JsonProperty(index = 8)
    private List<UUID> solutions;

    @JsonProperty(index = 9)
    private Topic topic;

    @JsonProperty(index = 10)
    private Integer timesFavorite;

    @JsonProperty(index = 11)
    private List<UUID> tags;

    @JsonProperty(index = 12)
    private Integer timesBookmark;

    @JsonProperty(index = 13)
    private Integer timesSolved;
    
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/dto/ChallengeDto.java:ChallengeDto.<init>
// Node: AllArgsConstructor
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

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/dto/ResourceDto.java:ResourceDto.<init>
// Node: Builder
package com.itachallenge.challenge.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.UUID;

@AllArgsConstructor
@NoArgsConstructor
@Getter
@Setter
public class TagDto {

    @JsonProperty(value = "id_tag", index = 0)
    private UUID tagId;

    @JsonProperty(value = "tag_name", index = 1)
    private String tagName;

    @JsonProperty(value = "tag_description", index = 2)
    private String tagDescription;

    @JsonProperty("language_id")
    private UUID languageId;

}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/dto/TagDto.java:TagDto.<init>
package com.itachallenge.challenge.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.*;
import org.springframework.stereotype.Component;

import java.util.Locale;
import java.util.Map;
import java.util.UUID;

@Component
@JsonInclude(JsonInclude.Include.NON_EMPTY)
@AllArgsConstructor(access = AccessLevel.PRIVATE)
@NoArgsConstructor
@Builder
@Getter
@Setter
public class ExampleDto {

    @JsonProperty(value = "example_id", index = 0)
    private UUID exampleId;

    @JsonProperty(value = "example_test", index = 1)
    private Map<Locale, String> exampleTest;

}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/dto/ExampleDto.java:ExampleDto.<init>
package com.itachallenge.challenge.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.*;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;

@Component
@JsonInclude(JsonInclude.Include.NON_EMPTY)
@AllArgsConstructor(access = AccessLevel.PUBLIC)
@NoArgsConstructor
@Builder
@Getter
@Setter
public class ChallengeListDto {

    @JsonProperty(value = "results", index = 0)
    @Builder.Default
    private List<ChallengeDto> results = new ArrayList<>();

    @JsonProperty(value = "total", index = 1)
    @Builder.Default
    private Integer total = 0;
}



// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/dto/ChallengeListDto.java:ChallengeListDto.<init>
package com.itachallenge.challenge.dto;

import com.itachallenge.challenge.enums.DifficultyLevel;
import com.itachallenge.challenge.enums.Topic;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

import java.util.List;
import java.util.UUID;

@AllArgsConstructor
@Builder
@Getter
@Setter
public class ChallengeCreateDto {

    @NotEmpty(message = "{challenge.title.notEmpty}")
    private String challengeTitle;

    @NotEmpty(message = "{challenge.description.notEmpty}")
    private String description;

    private DifficultyLevel level;

    @NotEmpty(message = "{challenge.language.notEmpty}")
    private String language;

    @NotEmpty(message = "{challenge.solution.notEmpty}")
    private String solution;

    @NotNull(message = "{challenge.topic.notNull}")
    private Topic topic;

    @NotEmpty(message = "{challenge.tags.notEmpty}")
    private List<UUID> tags;
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/dto/ChallengeCreateDto.java:ChallengeCreateDto.<init>
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


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/dto/LanguageDto.java:LanguageDto.<init>
// Node: JsonSetter
package com.itachallenge.challenge.dto.submission;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.itachallenge.submission.enums.SubmissionAction;
import jakarta.validation.constraints.NotNull;
import lombok.*;

import java.util.UUID;



@AllArgsConstructor
@NoArgsConstructor
@Getter
@Setter
@Builder
public class SubmissionActionRequestDto {

    @NotNull
    @JsonProperty(value = "uuid_challenge")
    private UUID challengeId;

    @NotNull
    @JsonProperty(value = "uuid_language")
    private UUID languageId;

    @NotNull
    @JsonProperty("action")
    private SubmissionAction action;

    @JsonProperty(value = "submission_text")
    private String submissionText;
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/dto/submission/SubmissionActionRequestDto.java:SubmissionActionRequestDto.<init>
package com.itachallenge.challenge.dto.submission;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.*;

@AllArgsConstructor
@NoArgsConstructor
@Getter
@Setter
@Builder
public class SubmissionDto {
    @JsonProperty(value = "uuid_user")
    private String userId;

    @JsonProperty(value = "uuid_challenge")
    private String challengeId;

    @JsonProperty(value = "uuid_language")
    private String languageId;

    @JsonProperty("status")
    private String status;

    @JsonProperty(value = "submission_text")
    private String submissionText;
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/dto/submission/SubmissionDto.java:SubmissionDto.<init>
package com.itachallenge.challenge.dto.submission;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.*;

@AllArgsConstructor
@NoArgsConstructor
@Getter
@Setter
@Builder
public class SubmissionActionResponseDto {

    @JsonProperty(value = "submission_text")
    private String submissionText;

    @JsonProperty(value = "is_solved")
    private Boolean isSolved;

    @JsonProperty(value = "times_solved")
    private Integer timesSolved;

    @JsonProperty("status")
    private String status;
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/dto/submission/SubmissionActionResponseDto.java:SubmissionActionResponseDto.<init>
