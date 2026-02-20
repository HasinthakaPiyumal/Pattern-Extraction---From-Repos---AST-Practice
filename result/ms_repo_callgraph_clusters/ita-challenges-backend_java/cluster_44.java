// Cluster 44

// Node: isValid
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


// Node: getDefaultConstraintMessageTemplate
// Node: disableDefaultConstraintViolation
// Node: buildConstraintViolationWithTemplate
// Node: addConstraintViolation
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



// Node: testValidUUID_ShouldReturnTrue
// Node: testNullUUID_ShouldReturnFalseAndSetMessage
// Node: testInvalidUUID_ShouldReturnFalseAndSetMessage
// Node: testEmptyUUID_ShouldReturnFalseAndSetMessage
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



// Node: shouldReturnTrueForValidUsername
// Node: shouldReturnFalseForNullUsername
// Node: shouldReturnFalseForEmptyString
// Node: shouldReturnFalseForTooLongUsername
// Node: repeat
// Node: shouldReturnFalseForInvalidCharacters
// Node: shouldReturnFalseForUsernameStartingOrEndingWithHyphen
// Node: shouldReturnTrueForMinimumLengthUsername
// Node: shouldReturnTrueForMaximumLengthUsername
package com.itachallenge.challenge.validator;

import com.itachallenge.challenge.annotations.ValidUUID;
import jakarta.validation.ConstraintValidator;
import jakarta.validation.ConstraintValidatorContext;

import java.util.UUID;

public class UUIDValidator implements ConstraintValidator<ValidUUID, UUID> {

    @Override
    public boolean isValid(UUID uuid, ConstraintValidatorContext context) {
        return uuid != null;
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


// Node: isNotValid
// Node: isTooLongNotValid
package com.itachallenge.challenge.validator;

import org.junit.jupiter.api.Test;

import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

public class UUIDValidatorTest {

    private final UUIDValidator validator = new UUIDValidator();

    @Test
    public void isValid_withNullUUID_returnsFalse() {
        assertFalse(validator.isValid(null, null));
    }

    @Test
    public void isValid_withValidUUID_returnsTrue() {
        assertTrue(validator.isValid(UUID.randomUUID(), null));
    }
}

// Node: isValid_withNullUUID_returnsFalse
// Node: isValid_withValidUUID_returnsTrue
