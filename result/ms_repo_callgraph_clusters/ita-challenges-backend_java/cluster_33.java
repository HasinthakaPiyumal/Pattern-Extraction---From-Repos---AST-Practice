// Cluster 33

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

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/challenge/validator/UUIDValidatorTest.java:UUIDValidatorTest.<init>
// Node: UUIDValidator
