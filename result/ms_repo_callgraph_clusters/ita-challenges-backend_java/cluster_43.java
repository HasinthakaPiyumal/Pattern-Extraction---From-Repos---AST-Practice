// Cluster 43

package com.itachallenge.errorcore.exceptionhandler;

import com.fasterxml.jackson.databind.exc.InvalidFormatException;
import com.itachallenge.errorcore.builder.ErrorResponseBuilder;
import com.itachallenge.errorcore.dto.APIErrorResponse;
import com.itachallenge.errorcore.exception.BaseApiException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.ConstraintViolationException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.core.codec.DecodingException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.web.server.ServerWebInputException;

@Slf4j
@RequiredArgsConstructor
@RestControllerAdvice
@Order(Ordered.LOWEST_PRECEDENCE)
public final class GlobalExceptionHandler {

    private final ErrorResponseBuilder responseBuilder;

    @ExceptionHandler(Exception.class)
    public ResponseEntity<APIErrorResponse> handleAny(Exception e, HttpServletRequest request) {
        log.error("Unexpected error happened: {}", e.getMessage());
        return ResponseEntity
                .status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(responseBuilder
                        .buildError(e, request)
                );
    }

    @ExceptionHandler(BaseApiException.class)
    public ResponseEntity<APIErrorResponse> handleApiCustomException(BaseApiException e, HttpServletRequest request){
        String exceptionName = e.getClass().getSimpleName();
        log.error("Custom exception happened [{}]: {}", exceptionName, e.getMessage());
        return ResponseEntity
                .status(e.getInfo().status())
                .body(responseBuilder
                        .buildCustomExceptionError(e, request)
                );
    }

    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<APIErrorResponse> handleIllegalArgument(IllegalArgumentException e, HttpServletRequest request) {
        log.error("Illegal argument happened: {}", e.getMessage());
        return ResponseEntity
                .status(HttpStatus.BAD_REQUEST)
                .body(responseBuilder
                        .buildError(e, request)
                );
    }

    @ExceptionHandler(ConstraintViolationException.class)
    public ResponseEntity<APIErrorResponse> handleValidationExceptions(ConstraintViolationException ex, HttpServletRequest request) {
        log.error("Validation error happened: {}", ex.getMessage());
        return ResponseEntity
                .status(HttpStatus.BAD_REQUEST)
                .body(responseBuilder
                        .buildConstraintViolationErrorResponse(ex,request)
                );
    }

    @ExceptionHandler(MethodArgumentTypeMismatchException.class)
    public ResponseEntity<APIErrorResponse> handleTypeMismatchException(MethodArgumentTypeMismatchException ex, HttpServletRequest request) {
        log.error("Type mismatch error happened: {}", ex.getMessage());
        return ResponseEntity
                .status(HttpStatus.BAD_REQUEST)
                .body(responseBuilder
                        .buildTypeMismatchErrorResponse(ex, request));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<APIErrorResponse> handleMethodArgumentNotValidException(
            MethodArgumentNotValidException ex,
            HttpServletRequest request) {
        log.error("Method argument not valid error happened: {}", ex.getMessage());
        return ResponseEntity
                .status(HttpStatus.BAD_REQUEST)
                .body(responseBuilder
                        .buildArgumentNotValidErrorResponse(ex, request));
    }

    @ExceptionHandler(ResponseStatusException.class)
    public ResponseEntity<APIErrorResponse> handleResponseStatusException(ResponseStatusException ex, HttpServletRequest request) {
        log.error("Status error happened: {}", ex.getMessage());
        return ResponseEntity
                .status(ex.getStatusCode())
                .body(responseBuilder
                        .buildStatusErrorResponse(ex, request));
    }

    @ExceptionHandler(InvalidFormatException.class)
    public ResponseEntity<APIErrorResponse> handleInvalidFormat(
            InvalidFormatException ex, HttpServletRequest request) {
        log.debug("Invalid format excetpion happened: {}", ex.getMessage());
        return ResponseEntity.badRequest()
                .body(responseBuilder.buildError(ex,request));
    }

    @ExceptionHandler({
            HttpMessageNotReadableException.class,
            ServerWebInputException.class,
            DecodingException.class
    })
    public ResponseEntity<APIErrorResponse> handleWebFluxBindingErrors(
            Exception ex, HttpServletRequest request) {

        Throwable root = ex.getCause();
        while (root != null) {
            if (root instanceof InvalidFormatException invalid) {
                return handleInvalidFormat(invalid, request);
            }
            root = root.getCause();
        }

        log.debug("Unhandled binding exception type: {}", ex.getClass().getSimpleName());
        return ResponseEntity.badRequest()
                .body(responseBuilder.buildError(ex,request));
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/error-response-core/src/main/java/com/itachallenge/errorcore/exceptionhandler/GlobalExceptionHandler.java:GlobalExceptionHandler.<init>
// Node: Order
package com.itachallenge.user.filter;

import com.itachallenge.user.config.PropertiesConfig;
import jakarta.servlet.*;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;

import java.io.IOException;

@Component
@Order(1)
@RequiredArgsConstructor
public class MaxLengthURIFilter implements Filter {

    private final PropertiesConfig prpsConfig;

    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain) throws IOException, ServletException {
        int totalURLLength;
        HttpServletRequest requestHttp = (HttpServletRequest) request;
        HttpServletResponse responseHttp = (HttpServletResponse) response;


        String requestURL = (requestHttp.getRequestURL() != null) ? requestHttp.getRequestURL().toString() : "";
        String queryString = requestHttp.getQueryString();

        int queryStringLength = (queryString != null) ? queryString.length() : 0;

        totalURLLength = requestURL.length() + queryStringLength;

        if (prpsConfig.getUrlMaxLength() < totalURLLength) {
            responseHttp.setStatus(HttpServletResponse.SC_REQUEST_URI_TOO_LONG);
        } else {
            chain.doFilter(request, response);
        }

    }

}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/filter/MaxLengthURIFilter.java:MaxLengthURIFilter.<init>
// Node: doFilter
// Node: getRequestURL
// Node: getQueryString
// Node: length
// Node: getUrlMaxLength
package com.itachallenge.user.filter;

import com.itachallenge.user.config.TomcatConfig;
import jakarta.servlet.*;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

import java.io.IOException;

@Component
@RequiredArgsConstructor
public class ContentLengthFilter implements Filter {

    private final TomcatConfig tomcatConfig;

    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException {
        if (request instanceof HttpServletRequest) {
            int contentLength = request.getContentLength();
            if (contentLength > tomcatConfig.getMaxHttpFormPostSize()) {
                throw new ServletException("Request body is too large!");
            }
        }
        chain.doFilter(request, response);
    }

}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/filter/ContentLengthFilter.java:ContentLengthFilter.<init>
// Node: getContentLength
// Node: getMaxHttpFormPostSize
// Node: ServletException
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


// Node: assertThrows
package com.itachallenge.user.filter;

import com.itachallenge.user.config.PropertiesConfig;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;

import java.io.IOException;

import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.mockito.Mockito.*;

class MaxLengthURIFilterTest {

    @Mock
    private PropertiesConfig prpsConfig;

    @Mock
    private HttpServletRequest request;

    @Mock
    private HttpServletResponse response;

    @Mock
    private FilterChain filterChain;

    @InjectMocks
    private MaxLengthURIFilter filter;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
    }

    @Test
    void doFilter_whenURILengthExceedsLimit_thenSetStatusToRequestURITooLong() throws ServletException, IOException {
        when(request.getRequestURL()).thenReturn(new StringBuffer("http://localhost:8080/some/path"));
        when(request.getQueryString()).thenReturn("query=long_string_that_exceeds_limit");
        when(prpsConfig.getUrlMaxLength()).thenReturn(50);

        filter.doFilter(request, response, filterChain);

        verify(response).setStatus(HttpServletResponse.SC_REQUEST_URI_TOO_LONG);
        verify(filterChain, never()).doFilter(request, response);
    }

    @Test
    void doFilter_whenURILengthIsWithinLimit_thenProceedWithChain() throws ServletException, IOException {
        when(request.getRequestURL()).thenReturn(new StringBuffer("http://localhost:8080/some/path"));
        when(request.getQueryString()).thenReturn("query=ok");
        when(prpsConfig.getUrlMaxLength()).thenReturn(500);

        filter.doFilter(request, response, filterChain);

        verify(response, never()).setStatus(anyInt());
        verify(filterChain).doFilter(request, response);
    }
    @Test
    void doFilter_whenURIisNull_thenProceedWithChain() throws ServletException, IOException {
        when(request.getRequestURL()).thenReturn(null);
        when(request.getQueryString()).thenReturn(null);
        when(prpsConfig.getUrlMaxLength()).thenReturn(50);

        assertDoesNotThrow(() -> filter.doFilter(request, response, filterChain));
        verify(filterChain).doFilter(request, response);
}
}

// Node: doFilter_whenURILengthExceedsLimit_thenSetStatusToRequestURITooLong
// Node: StringBuffer
// Node: doFilter_whenURILengthIsWithinLimit_thenProceedWithChain
// Node: anyInt
// Node: doFilter_whenURIisNull_thenProceedWithChain
// Node: assertDoesNotThrow
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

// Node: doFilter_whenContentLengthExceedsLimit_thenThrowServletException
// Node: doFilter_whenContentLengthIsWithinLimit_thenProceedWithChain
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


// Node: shouldReturnNullWhenInputIsNull
// Node: shouldReturnNullWhenValueDoesNotExist
// Node: validateRoleChange
package com.itachallenge.auth.enums;

import com.itachallenge.auth.exception.InvalidRoleChangeRequestException;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class UserRoleTest {

    @Test
    void validateRoleChange_validChange_ADMIN_to_USER_shouldPass() {
        assertDoesNotThrow(() -> UserRole.validateRoleChange("ADMIN", "USER"));
    }

    @Test
    void validateRoleChange_validChange_USER_to_ADMIN_shouldPass() {
        assertDoesNotThrow(() -> UserRole.validateRoleChange("user", "admin"));
    }

    @Test
    void validateRoleChange_nullRequestedRole_shouldThrow() {
        InvalidRoleChangeRequestException ex = assertThrows(
                InvalidRoleChangeRequestException.class,
                () -> UserRole.validateRoleChange("ADMIN", null)
        );
        assertEquals("New role must be provided.", ex.getMessage());
    }

    @Test
    void validateRoleChange_blankRequestedRole_shouldThrow() {
        InvalidRoleChangeRequestException ex = assertThrows(
                InvalidRoleChangeRequestException.class,
                () -> UserRole.validateRoleChange("ADMIN", " ")
        );
        assertEquals("New role must be provided.", ex.getMessage());
    }

    @Test
    void validateRoleChange_invalidRequestedRole_shouldThrow() {
        InvalidRoleChangeRequestException ex = assertThrows(
                InvalidRoleChangeRequestException.class,
                () -> UserRole.validateRoleChange("ADMIN", "GUEST")
        );
        assertEquals("Requested role change is not allowed.", ex.getMessage());
    }

    @Test
    void validateRoleChange_sameRole_shouldThrow() {
        InvalidRoleChangeRequestException ex = assertThrows(
                InvalidRoleChangeRequestException.class,
                () -> UserRole.validateRoleChange("USER", "user")
        );
        assertEquals("New role is the same as current role.", ex.getMessage());
    }

    @Test
    void validateRoleChange_invalidCurrentRole_shouldThrow() {
        InvalidRoleChangeRequestException ex = assertThrows(
                InvalidRoleChangeRequestException.class,
                () -> UserRole.validateRoleChange("GUEST", "ADMIN")
        );
        assertEquals("Current role is not allowed.", ex.getMessage());
    }

    @Test
    void validateRoleChange_nullCurrentRole_shouldThrow() {
        InvalidRoleChangeRequestException ex = assertThrows(
                InvalidRoleChangeRequestException.class,
                () -> UserRole.validateRoleChange(null, "ADMIN")
        );
        assertEquals("Current role must be provided.", ex.getMessage());
    }

    @Test
    void validateRoleChange_invalidRequested_shouldThrow() {
        InvalidRoleChangeRequestException ex = assertThrows(
                InvalidRoleChangeRequestException.class,
                () -> UserRole.validateRoleChange("ADMIN", "GUEST")
        );
        assertEquals("Requested role change is not allowed.", ex.getMessage());
    }

    @Test
    void validateRoleChange_notAllowedTransition_shouldThrow() {
        InvalidRoleChangeRequestException ex = assertThrows(
                InvalidRoleChangeRequestException.class,
                () -> UserRole.validateRoleChange("ADMIN", "GUEST")
        );
        assertEquals("Requested role change is not allowed.", ex.getMessage());
    }

    @Test
    void validateAdminRoleChange_invalidTransition_shouldThrow() {
        InvalidRoleChangeRequestException ex = assertThrows(
                InvalidRoleChangeRequestException.class,
                () -> UserRole.validateRoleChange("ADMIN", "ADMIN")
        );
        assertEquals("New role is the same as current role.", ex.getMessage());
    }

    @Test
    void validateUserRoleChange_invalidTransition_shouldThrow() {
        InvalidRoleChangeRequestException ex = assertThrows(
                InvalidRoleChangeRequestException.class,
                () -> UserRole.validateRoleChange("USER", "USER")
        );
        assertEquals("New role is the same as current role.", ex.getMessage());
    }

    @Test
    void validateRoleChange_userToAdmin_thenAdminToUserAllowed_butOtherDirectionRejected() {
        assertDoesNotThrow(() -> UserRole.validateRoleChange("USER", "ADMIN"));

        assertDoesNotThrow(() -> UserRole.validateRoleChange("ADMIN", "USER"));

        InvalidRoleChangeRequestException ex = assertThrows(
                InvalidRoleChangeRequestException.class,
                () -> UserRole.validateRoleChange("ADMIN", "ADMIN")
        );
        assertEquals("New role is the same as current role.", ex.getMessage());
    }

}

// Node: validateRoleChange_validChange_ADMIN_to_USER_shouldPass
// Node: validateRoleChange_validChange_USER_to_ADMIN_shouldPass
// Node: validateRoleChange_nullRequestedRole_shouldThrow
// Node: validateRoleChange_blankRequestedRole_shouldThrow
// Node: validateRoleChange_invalidRequestedRole_shouldThrow
// Node: validateRoleChange_sameRole_shouldThrow
// Node: validateRoleChange_invalidCurrentRole_shouldThrow
// Node: validateRoleChange_nullCurrentRole_shouldThrow
// Node: validateRoleChange_invalidRequested_shouldThrow
// Node: validateRoleChange_notAllowedTransition_shouldThrow
// Node: validateAdminRoleChange_invalidTransition_shouldThrow
// Node: validateUserRoleChange_invalidTransition_shouldThrow
// Node: validateRoleChange_userToAdmin_thenAdminToUserAllowed_butOtherDirectionRejected
