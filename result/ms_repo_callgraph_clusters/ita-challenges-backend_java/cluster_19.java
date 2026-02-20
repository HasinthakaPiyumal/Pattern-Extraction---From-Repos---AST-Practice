// Cluster 19

package com.itachallenge.document.controller;

import org.junit.jupiter.api.Test;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.redirectedUrl;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

class ApiDocsControllerTest {

    @Test
    void testGetApiDocs() throws Exception {

        ApiDocsController apiDocsController = new ApiDocsController();

        MockMvc mockMvc = MockMvcBuilders.standaloneSetup(apiDocsController).build();

        mockMvc.perform(get("/api-docs/all"))
                .andExpect(status().is3xxRedirection())
                .andExpect(redirectedUrl("/api-docs"));
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-document/src/test/java/com/itachallenge/document/controller/ApiDocsControllerTest.java:ApiDocsControllerTest.<init>
// Node: testGetApiDocs
// Node: ApiDocsController
// Node: standaloneSetup
// Node: perform
// Node: andExpect
// Node: is3xxRedirection
// Node: redirectedUrl
package com.itachallenge.user.annotations;

import com.itachallenge.user.validator.GithubUsernameValidator;

import javax.validation.Constraint;
import javax.validation.Payload;
import java.lang.annotation.*;

@Documented
@Constraint(validatedBy = GithubUsernameValidator.class)
@Target({ElementType.FIELD, ElementType.PARAMETER})
@Retention(RetentionPolicy.RUNTIME)
public @interface ValidGithubUsername {
    String message() default "Invalid GitHub username format. Must be 1-39 characters long, alphanumeric or hyphen, and cannot start/end with a hyphen.";

    Class<?>[] groups() default {};

    Class<? extends Payload>[] payload() default {};
}



// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/annotations/ValidGithubUsername.java:ValidGithubUsername.<init>
// Node: Constraint
// Node: Target
// Node: Retention
// Node: groups
// Node: payload
package com.itachallenge.user.annotations;

import com.itachallenge.user.validator.GenericUUIDValidator;
import jakarta.validation.Constraint;
import jakarta.validation.Payload;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

@Target({ElementType.FIELD, ElementType.PARAMETER})
@Retention(RetentionPolicy.RUNTIME)
@Constraint(validatedBy = GenericUUIDValidator.class)
public @interface GenericUUIDValid {
    String message() default "UUID is invalid";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};

    String pattern() default ""; // Optional
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/annotations/GenericUUIDValid.java:GenericUUIDValid.<init>
// Node: pattern
package com.itachallenge.challenge.annotations;

import com.itachallenge.challenge.validator.UUIDValidator;
import jakarta.validation.Constraint;
import jakarta.validation.Payload;
import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

@Constraint(validatedBy = UUIDValidator.class)
@Target({ElementType.FIELD})
@Retention(RetentionPolicy.RUNTIME)
public @interface ValidUUID {
    String message() default "Invalid UUID";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
}

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/annotations/ValidUUID.java:ValidUUID.<init>
package com.itachallenge.challenge.annotations;


import com.itachallenge.challenge.validator.GenericPatternValidator;
import jakarta.validation.Constraint;
import jakarta.validation.Payload;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

@Target({ElementType.FIELD, ElementType.PARAMETER})
@Retention(RetentionPolicy.RUNTIME)
@Constraint(validatedBy = GenericPatternValidator.class)
public @interface ValidGenericPattern {
    String message() default "The value is invalid.";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
    String pattern() default ""; // Optional
}

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/annotations/ValidGenericPattern.java:ValidGenericPattern.<init>
