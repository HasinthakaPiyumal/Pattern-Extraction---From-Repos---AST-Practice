// Cluster 31

package com.itachallenge.jwtcore.service;

import io.jsonwebtoken.Claims;
import javax.crypto.SecretKey;

public interface IJwtService {
    SecretKey getSigningKey();
    String generateToken(String username, String role, String uuid);
    void validateToken(String token);
    Claims extractAllClaims(String token);
    String extractBearerToken(String authHeader);
    String getUserUuIdFromAuthenticationHeader(String authHeader);

}

// Node: repos/cloned_ms_repos/ita-challenges-backend/jwt-core/src/main/java/com/itachallenge/jwtcore/service/IJwtService.java:IJwtService.<init>
// Node: getSigningKey
// Node: generateToken
// Node: extractAllClaims
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

// Node: subject
// Node: claim
// Node: issuedAt
// Node: Date
// Node: expiration
// Node: currentTimeMillis
// Node: signWith
// Node: compact
// Node: parser
// Node: verifyWith
// Node: parseSignedClaims
// Node: ExpiredJwtException
// Node: getClaims
// Node: decode
// Node: hmacShaKeyFor
// Node: getPayload
// Node: getExpiration
// Node: getSubject
package com.itachallenge.jwtcore.service;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.JwtException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.assertj.core.api.AssertionsForClassTypes.assertThatExceptionOfType;

class JwtServiceUuidExtractionTest {

    private JwtService jwtService;

    private final String jwtSigningKey = "bXlTZWNyZXRTaWduaW5nS2V5V2hpY2hJc1ZlcnlTZWN1cmVBbmRub2JvZHlDb3VsZEd1ZXNz";
    private final long minutesTillExpiration = 10L;

    @BeforeEach
    void setUp() {
        jwtService = new JwtService(jwtSigningKey, minutesTillExpiration);
    }

    @Test
    void getUserUuidFromValidAuthorizationHeader_ShouldReturnUuid() {
        String uuid = "test-uuid-123";
        String token = jwtService.generateToken("testUser", "USER", uuid);
        String authHeader = "Bearer " + token;

        Claims claims = jwtService.extractAllClaims(jwtService.extractBearerToken(authHeader));
        String extractedUuid = claims.get("uuid", String.class);

        assertThat(extractedUuid).isEqualTo(uuid);
    }

    @Test
    void extractBearerToken_WithNullHeader_ShouldThrowException() {
        assertThatThrownBy(() -> jwtService.extractBearerToken(null))
                .isInstanceOf(JwtException.class)
                .hasMessage("Authorization header is missing or malformed");
    }

    @Test
    void extractBearerToken_WithMalformedHeader_ShouldThrowException() {
        String malformedHeader = "Token xyz.abc.def";
        assertThatThrownBy(() -> jwtService.extractBearerToken(malformedHeader))
                .isInstanceOf(JwtException.class)
                .hasMessage("Authorization header is missing or malformed");
    }

    @Test
    void extractAllClaims_WithInvalidToken_ShouldThrowJwtException() {
        String invalidToken = "invalid.token.here";
        assertThatThrownBy(() -> jwtService.extractAllClaims(invalidToken))
                .isInstanceOf(JwtException.class)
                .hasMessageContaining("Invalid or tampered token");
    }

    @Test
    void getUserUuIdFromAuthenticationHeader_validToken_returnsUuid() {
        String uuid = "uuid-1234";
        String token = jwtService.generateToken("testuser", "USER", uuid);
        String authHeader = "Bearer " + token;

        String result = jwtService.getUserUuIdFromAuthenticationHeader(authHeader);

        assertThat(result).isEqualTo(uuid);
    }

    @Test
    void getUserUuIdFromAuthenticationHeader_nullHeader_throwsJwtException() {
        assertThatThrownBy(() -> jwtService.getUserUuIdFromAuthenticationHeader(null))
                .isInstanceOf(JwtException.class)
                .hasMessageContaining("Missing or bad formatted Authorization header");
    }

    @Test
    void getUserUuIdFromAuthenticationHeader_malformedHeader_throwsJwtException() {
        assertThatThrownBy(() -> jwtService.getUserUuIdFromAuthenticationHeader("Token something"))
                .isInstanceOf(JwtException.class)
                .hasMessageContaining("Missing or bad formatted Authorization header");
    }

    @Test
    void getUserUuIdFromAuthenticationHeader_invalidToken_throwsJwtException() {
        String invalidToken = "Bearer invalid.token.value";
        assertThatThrownBy(() -> jwtService.getUserUuIdFromAuthenticationHeader(invalidToken))
                .isInstanceOf(JwtException.class)
                .hasMessageContaining("Invalid Authorization header content");
    }

    @Test
    void extractUuid_invalidToken_returnsNull() {
        String result = invokeExtractUuid("invalid.token.structure");
        assertThat(result).isNull();
    }

    // Acceso al método privado mediante reflexión
    private String invokeExtractUuid(String token) {
        try {
            var method = JwtService.class.getDeclaredMethod("extractUuid", String.class);
            method.setAccessible(true);
            return (String) method.invoke(jwtService, token);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    @Test
    void extractAllClaims_validToken_returnsClaims() throws IOException, NoSuchMethodException, InvocationTargetException, IllegalAccessException {
        String token = jwtService.generateToken("testuser", "USER", "uuid-9876");
        Claims claims = jwtService.extractAllClaims(token);

        assertThat(claims).isNotNull();
        assertThat(claims.get("sub")).isEqualTo("testuser");
        assertThat(claims.get("role")).isEqualTo("USER");
        assertThat(claims.get("uuid")).isEqualTo("uuid-9876");
    }

    @Test
    void extractAllClaims_invalidToken_throwsException() {
        String invalidToken = "malformed.token.string"; // An invalid JWT string

        assertThatExceptionOfType(JwtException.class)
                .isThrownBy(() -> jwtService.extractAllClaims(invalidToken))
                .withMessageContaining("Invalid or tampered token");
    }


}


// Node: getUserUuidFromValidAuthorizationHeader_ShouldReturnUuid
// Node: assertThat
// Node: getUserUuIdFromAuthenticationHeader_validToken_returnsUuid
// Node: extractUuid_invalidToken_returnsNull
// Node: invokeExtractUuid
// Node: isNull
// Node: getDeclaredMethod
// Node: setAccessible
// Node: invoke
// Node: extractAllClaims_validToken_returnsClaims
// Node: isNotNull
// Node: extractAllClaims_invalidToken_throwsException
// Node: assertThatExceptionOfType
// Node: isThrownBy
// Node: withMessageContaining
package com.itachallenge.jwtcore.service;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.Date;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class JwtServiceTest {

    private JwtService jwtService;

    // Clave en Base64, válida para HMAC-SHA con al menos 256 bits
    private final String jwtSigningKey = "bXlTZWNyZXRTaWduaW5nS2V5V2hpY2hJc1ZlcnlTZWN1cmVBbmRub2JvZHlDb3VsZEd1ZXNz";
    private final long minutesTillExpiration = 10L;

    @BeforeEach
    void setUp() {
        jwtService = new JwtService(jwtSigningKey, minutesTillExpiration);
    }

    @Test
    void generateToken_ShouldReturnValidJwt() {
        String username = "testUser";
        String role = "ADMIN";
        String uuid = "uuid";

        String token = jwtService.generateToken(username, role, uuid);

        assertThat(token).isNotNull().isNotEmpty();

        Claims claims = Jwts.parser()
                .verifyWith(Keys.hmacShaKeyFor(io.jsonwebtoken.io.Decoders.BASE64.decode(jwtSigningKey)))
                .build()
                .parseSignedClaims(token)
                .getPayload();

        assertThat(claims.getSubject()).isEqualTo(username);
        assertThat(claims.get("role", String.class)).isEqualTo(role);
        assertThat(claims.get("uuid", String.class)).isEqualTo(uuid);
        assertThat(claims.getExpiration()).isAfter(new Date());
    }

    @Test
    void generateToken_ShouldHaveCorrectExpirationTime() {
        String username = "testUser";
        String role = "USER";
        String uuid = "uuid";
        long expectedExpirationMillis = System.currentTimeMillis() + (minutesTillExpiration * 60000);

        String token = jwtService.generateToken(username, role, uuid);

        Claims claims = Jwts.parser()
                .verifyWith(Keys.hmacShaKeyFor(io.jsonwebtoken.io.Decoders.BASE64.decode(jwtSigningKey)))
                .build()
                .parseSignedClaims(token)
                .getPayload();

        long actualExpirationMillis = claims.getExpiration().getTime();
        assertThat(actualExpirationMillis)
                .isBetween(expectedExpirationMillis - 5000, expectedExpirationMillis + 5000); // margen de 5s
    }

    @Test
    void validateToken_WithValidToken_DoesNotThrow() {
        String token = jwtService.generateToken("testUser", "USER", "uuid-1234");
        jwtService.validateToken(token); // No debe lanzar excepción
    }

    @Test
    void validateToken_WithInvalidToken_ShouldThrowJwtException() {
        String invalidToken = "this.is.an.invalid.token";
        assertThatThrownBy(() -> jwtService.validateToken(invalidToken))
                .isInstanceOf(JwtException.class)
                .hasMessageContaining("Invalid or tampered token");
    }

    @Test
    void validateToken_WithExpiredToken_ShouldThrowExpiredJwtException() {
        JwtService shortLivedService = new JwtService(jwtSigningKey, 0L); // 0 min duración
        String token = shortLivedService.generateToken("expiredUser", "USER", "uuid");
        try {
            Thread.sleep(1000); // Esperar 1 segundo para garantizar que expire
        } catch (InterruptedException ignored) {}

        assertThatThrownBy(() -> shortLivedService.validateToken(token))
                .isInstanceOf(ExpiredJwtException.class)
                .hasMessageContaining("Token expired but logout successful");
    }

    @Test
    void extractBearerToken_WithValidHeader_ReturnsToken() {
        String token = "abc.def.ghi";
        String header = "Bearer " + token;

        String result = jwtService.extractBearerToken(header);

        assertThat(result).isEqualTo(token);
    }

    @Test
    void extractBearerToken_WithNullHeader_ThrowsJwtException() {
        assertThatThrownBy(() -> jwtService.extractBearerToken(null))
                .isInstanceOf(JwtException.class)
                .hasMessage("Authorization header is missing or malformed");
    }

    @Test
    void extractBearerToken_WithMalformedHeader_ThrowsJwtException() {
        String malformedHeader = "Token abc.def.ghi";

        assertThatThrownBy(() -> jwtService.extractBearerToken(malformedHeader))
                .isInstanceOf(JwtException.class)
                .hasMessage("Authorization header is missing or malformed");
    }

    @Test
    void extractAllClaims_WithValidToken_ShouldReturnClaims() {
        String token = jwtService.generateToken("testUser", "USER", "uuid-123");
        Claims claims = jwtService.extractAllClaims(token);

        assertThat(claims.getSubject()).isEqualTo("testUser");
        assertThat(claims.get("role", String.class)).isEqualTo("USER");
        assertThat(claims.get("uuid", String.class)).isEqualTo("uuid-123");
    }

    @Test
    void extractAllClaims_WithExpiredToken_ShouldThrowExpiredJwtException() {
        JwtService shortLivedJwtService = new JwtService(jwtSigningKey, 0L);
        String token = shortLivedJwtService.generateToken("expiredUser", "USER", "uuid-456");

        try {
            Thread.sleep(1000);
        } catch (InterruptedException ignored) {}

        assertThatThrownBy(() -> shortLivedJwtService.extractAllClaims(token))
                .isInstanceOf(ExpiredJwtException.class)
                .hasMessageContaining("Token expired");
    }

    @Test
    void extractAllClaims_WithInvalidToken_ShouldThrowJwtException() {
        String invalidToken = "this.is.not.valid";

        assertThatThrownBy(() -> jwtService.extractAllClaims(invalidToken))
                .isInstanceOf(JwtException.class)
                .hasMessageContaining("Invalid or tampered token");
    }

}


// Node: generateToken_ShouldReturnValidJwt
// Node: isNotEmpty
// Node: isAfter
// Node: generateToken_ShouldHaveCorrectExpirationTime
// Node: getTime
// Node: isBetween
// Node: extractAllClaims_WithValidToken_ShouldReturnClaims
// Node: toUpperCase
// Node: getStatusCode
// Node: getBody
// Node: status
// Node: getInfo
package com.itachallenge.githubcore.exception;

public class GithubUnavailableException extends RuntimeException {
    public GithubUnavailableException(String message) {
        super(message);
    }

    public GithubUnavailableException(String message, Throwable cause) {
        super(message, cause);
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/github-core/src/main/java/com/itachallenge/githubcore/exception/GithubUnavailableException.java:GithubUnavailableException.<init>
// Node: GithubUnavailableException
// Node: setup
package com.itachallenge.errorcore.builder;


import com.fasterxml.jackson.databind.exc.InvalidFormatException;
import com.itachallenge.errorcore.dto.APIErrorResponse;
import com.itachallenge.errorcore.dto.FieldErrorDto;
import com.itachallenge.errorcore.exception.BaseApiException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.ConstraintViolation;
import jakarta.validation.ConstraintViolationException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.MessageSource;
import org.springframework.context.i18n.LocaleContextHolder;
import org.springframework.core.codec.DecodingException;
import org.springframework.http.HttpStatus;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.web.server.ServerWebInputException;

import java.util.List;
import java.util.Locale;

@Slf4j
@RequiredArgsConstructor
public class ErrorResponseBuilder {

    private final MessageSource messageSource;

    /** Build general error response.*/
    public APIErrorResponse buildError(
            Exception e,
            HttpServletRequest request
    ) {
        ExceptionMapping mapping = mapException(e);
        return APIErrorResponse.builder()
                .status(mapping.status.value())
                .error(mapping.status.getReasonPhrase())
                .message(resolveMessage(mapping.messageKey))
                .path(request != null ? request.getRequestURI() : null)
                .build();
    }

    public APIErrorResponse buildCustomExceptionError(
            BaseApiException e,
            HttpServletRequest request
    ) {
        ExceptionMapping mapping = mapException(e);
        return APIErrorResponse.builder()
                .status(mapping.status.value())
                .error(mapping.status.getReasonPhrase())
                .message(resolveMessage(mapping.messageKey,e.getInfo().messageArgs()))
                .path(request != null ? request.getRequestURI() : null)
                .build();
    }

    public APIErrorResponse buildArgumentNotValidErrorResponse(MethodArgumentNotValidException ex, HttpServletRequest request) {
        String objectName = ex.getBindingResult().getObjectName();
        return buildValidationErrorResponse(
                resolveMessage(mapException(ex).messageKey,objectName),
                extractFieldErrors(ex),
                request
        );
    }

    public APIErrorResponse buildConstraintViolationErrorResponse(ConstraintViolationException ex, HttpServletRequest request) {
        return buildValidationErrorResponse(
                resolveMessage(mapException(ex).messageKey),
                extractConstraintViolations(ex),
                request
        );
    }

    public APIErrorResponse buildTypeMismatchErrorResponse(MethodArgumentTypeMismatchException ex, HttpServletRequest request) {
        return buildValidationErrorResponse(
                resolveMessage(
                        mapException(ex).messageKey,
                        ex.getName(),                                   // {0} parameter name
                        ex.getValue(),                                  // {1} invalid value
                        ex.getRequiredType() != null
                                ? ex.getRequiredType().getSimpleName()
                                : "unknown"                                 // {2} expected type
                ),
                singleFieldErrorList(ex),
                request
        );
    }

    public APIErrorResponse buildStatusErrorResponse(ResponseStatusException ex, HttpServletRequest request) {
        HttpStatusCode statusCode = ex.getStatusCode();
        String errorMessage = resolveMessage(mapException(ex).messageKey);
        // Build the APIErrorResponse using your builder (same message text)
        return APIErrorResponse.builder()
                .status(statusCode.value())
                .error(ex.getReason())
                .message(errorMessage)
                .path(request != null ? request.getRequestURI() : null)
                .build();
    }

    // --- PRIVATE HELPERS ----------------------------------------------------
    /** Converts a validation violation into a detailed field error DTO. */
    private FieldErrorDto toFieldErrorDto(ConstraintViolation<?> violation) {
        String fieldName = extractFieldName(violation);
        String detailedMessage = resolveMessage(
                "validation.constraint.detailed",
                fieldName,
                violation.getMessage()
        );
        return FieldErrorDto.builder()
                .objectName(violation.getRootBeanClass().getSimpleName())
                .field(fieldName)
                .message(detailedMessage)
                .build();
    }

    /** Extracts field-level errors from @Valid annotated DTOs. */
    private List<FieldErrorDto> extractFieldErrors(MethodArgumentNotValidException ex) {
        Locale locale = LocaleContextHolder.getLocale();
        return ex.getBindingResult()
                .getFieldErrors()
                .stream()
                .map(error -> FieldErrorDto.builder()
                        .objectName(error.getObjectName())
                        .field(error.getField())
                        .message(messageSource.getMessage(error, locale))
                        .build())
                .toList();
    }

    /** Extracts constraint violations from @Validated annotated method parameters. */
    private List<FieldErrorDto> extractConstraintViolations(ConstraintViolationException ex) {
        return ex.getConstraintViolations()
                .stream()
                .map(this::toFieldErrorDto)
                .toList();
    }

    /** Creates a singleton list of FieldErrorDto for type mismatch or single-parameter errors. */
    private List<FieldErrorDto> singleFieldErrorList(MethodArgumentTypeMismatchException ex) {
        String field = ex.getName();
        String rejectedValue = ex.getValue() != null ? ex.getValue().toString() : "null";
        String requiredType = ex.getRequiredType() != null ? ex.getRequiredType().getSimpleName() : "unknown";

        FieldErrorDto fieldError = FieldErrorDto.builder()
                .objectName(ex.getParameter().getContainingClass().getSimpleName())
                .field(field)
                .message(resolveMessage(mapException(ex).messageKey,
                        field,
                        rejectedValue,
                        requiredType)
                )
                .build();

        return List.of(fieldError);
    }

    /** Extracts the last segment of the property path (the field name). */
    private String extractFieldName(ConstraintViolation<?> violation) {
        return violation.getPropertyPath().toString()
                .replaceAll("^.*\\.", ""); // e.g., user.email -> email
    }

    /** Build validation error response.*/
    private APIErrorResponse buildValidationErrorResponse(
            String message,
            List<FieldErrorDto> fieldErrors,
            HttpServletRequest request
    ) {
        return APIErrorResponse.builder()
                .status(HttpStatus.BAD_REQUEST.value())
                .error(HttpStatus.BAD_REQUEST.getReasonPhrase())
                .message(message)
                .errors(fieldErrors)
                .path(request != null ? request.getRequestURI() : null)
                .build();
    }

    /** Resolve message from message source. */
    public String resolveMessage(String messageKey) {
        return resolveMessage(messageKey, new Object[]{});
    }
    private String resolveMessage(String messageKey, Object arg1) {
        return resolveMessage(messageKey, new Object[]{arg1});
    }
    private String resolveMessage(String messageKey, Object arg1, Object arg2) {
        return resolveMessage(messageKey, new Object[]{arg1, arg2});
    }
    private String resolveMessage(String messageKey, Object arg1, Object arg2, Object arg3) {
        return resolveMessage(messageKey, new Object[]{arg1, arg2, arg3});
    }
    private String resolveMessage(String messageKey, Object[] args) {
        Locale locale = LocaleContextHolder.getLocale();
        try {
            return messageSource.getMessage(messageKey, args, locale);
        } catch (Exception e) {
            log.debug("No message found for key '{}', using literal", messageKey);
            return messageKey; // fallback to literal if no translation found
        }
    }

    // --- Exception Mapping----------------------------------------------------

    /** Internal record representing the mapping of an exception to a message key and HTTP status. */
    private record ExceptionMapping(HttpStatus status, String messageKey) {}

    /** Determines the appropriate message key and HTTP status for a given exception. */
    private ExceptionMapping mapException(Exception e) {
        // --- Validation & argument errors ---
        if (e instanceof BaseApiException bae)
            return new ExceptionMapping(bae.getInfo().status(), bae.getInfo().messageKey());

        if (e instanceof MethodArgumentNotValidException)
            return new ExceptionMapping(HttpStatus.BAD_REQUEST, "validation.argument_not_valid");

        if (e instanceof ConstraintViolationException)
            return new ExceptionMapping(HttpStatus.BAD_REQUEST, "validation.constraint");

        if (e instanceof MethodArgumentTypeMismatchException)
            return new ExceptionMapping(HttpStatus.BAD_REQUEST, "validation.type_mismatch");

        if (e instanceof IllegalArgumentException)
            return new ExceptionMapping(HttpStatus.BAD_REQUEST, "validation.illegal_argument");

        if (e instanceof InvalidFormatException
                || e instanceof HttpMessageNotReadableException
                || e instanceof ServerWebInputException
                || e instanceof DecodingException)
            return new ExceptionMapping(HttpStatus.BAD_REQUEST, "validation.bad_request");

        // --- ResponseStatusException (explicit HTTP semantics) ---
        if (e instanceof ResponseStatusException rse)
            return new ExceptionMapping(HttpStatus.valueOf(rse.getStatusCode().value()),
                    "status.exception." + rse.getStatusCode().value());
        // --- Default / fallback case ---
        log.warn("Unhandled exception type in ErrorResponseBuilder: {}", e.getClass().getName());
        return new ExceptionMapping(HttpStatus.INTERNAL_SERVER_ERROR, "internal.server_error");
    }

}


// Node: repos/cloned_ms_repos/ita-challenges-backend/error-response-core/src/main/java/com/itachallenge/errorcore/builder/ErrorResponseBuilder.java:ErrorResponseBuilder.<init>
// Node: buildError
// Node: mapException
// Node: getReasonPhrase
// Node: message
// Node: resolveMessage
// Node: path
// Node: getRequestURI
// Node: buildCustomExceptionError
// Node: messageArgs
// Node: buildArgumentNotValidErrorResponse
// Node: getBindingResult
// Node: getObjectName
// Node: buildValidationErrorResponse
// Node: extractFieldErrors
// Node: buildConstraintViolationErrorResponse
// Node: extractConstraintViolations
// Node: buildTypeMismatchErrorResponse
// Node: getName
// Node: getValue
// Node: getRequiredType
// Node: getSimpleName
// Node: singleFieldErrorList
// Node: buildStatusErrorResponse
// Node: getReason
// Node: toFieldErrorDto
// Node: extractFieldName
// Node: objectName
// Node: getRootBeanClass
// Node: field
// Node: getLocale
// Node: getFieldErrors
// Node: getField
// Node: getConstraintViolations
// Node: getParameter
// Node: getContainingClass
// Node: repos/cloned_ms_repos/ita-challenges-backend/error-response-core/src/main/java/com/itachallenge/errorcore/builder/ErrorResponseBuilder.java:ErrorResponseBuilder.extractFieldName
// Node: getPropertyPath
// Node: replaceAll
// Node: errors
// Node: ExceptionMapping
// Node: messageKey
// Node: ResponseStatusException
// Node: getClass
// Node: ExceptionHandler
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


// Node: handleAny
// Node: body
// Node: handleApiCustomException
// Node: handleIllegalArgument
// Node: handleValidationExceptions
// Node: handleTypeMismatchException
// Node: handleMethodArgumentNotValidException
// Node: handleResponseStatusException
// Node: handleInvalidFormat
// Node: badRequest
// Node: handleWebFluxBindingErrors
// Node: getCause
package com.itachallenge.errorcore.config;

import com.itachallenge.errorcore.builder.ErrorResponseBuilder;
import com.itachallenge.errorcore.exceptionhandler.GlobalExceptionHandler;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.context.MessageSource;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.support.ReloadableResourceBundleMessageSource;

/**
 * Manual configuration exposing shared error-handling components.
 */
@Configuration
public class ErrorHandlingConfig {

    @Bean
    public MessageSource messageSource() {
        ReloadableResourceBundleMessageSource src = new ReloadableResourceBundleMessageSource();
        src.setBasenames("classpath:core-messages", "classpath:messages");
        src.setDefaultEncoding("UTF-8");
        src.setFallbackToSystemLocale(false);
        return src;
    }

    @Bean
    public ErrorResponseBuilder errorResponseBuilder(MessageSource messageSource) {
        return new ErrorResponseBuilder(messageSource);
    }

    @Bean
    @ConditionalOnMissingBean(GlobalExceptionHandler.class)
    public GlobalExceptionHandler globalExceptionHandler(ErrorResponseBuilder builder) {
        // Anonymous subclass to register handler logic, if needed
        return new GlobalExceptionHandler(builder);
    }
}


// Node: globalExceptionHandler
// Node: GlobalExceptionHandler
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


// Node: TestDto
// Node: mock
// Node: buildError_shouldBuildBasicResponseWithRealMessage
// Node: DecodingException
// Node: getError
// Node: contains
// Node: getPath
// Node: buildTypeMismatchErrorResponse_shouldIncludeFieldInformation
// Node: MethodParameter
// Node: MethodArgumentTypeMismatchException
// Node: IllegalArgumentException
// Node: getErrors
// Node: getFirst
// Node: buildConstraintViolationErrorResponse_shouldBuildWithViolations
// Node: ConstraintViolationException
// Node: buildArgumentNotValidErrorResponse_shouldExtractFieldErrorsWithRealMessageSource
// Node: BeanPropertyBindingResult
// Node: rejectValue
// Node: MethodArgumentNotValidException
// Node: buildStatusErrorResponse_shouldUseAppropriateMessageWhen404
// Node: buildStatusErrorResponse_shouldUseAppropriateMessageWhen400
// Node: buildNotFoundError_shouldReturnNotFoundResponse
// Node: GenericNotFoundException
// Node: getTimestamp
package com.itachallenge.errorcore.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class FieldErrorDtoTest {

    private ObjectMapper objectMapper;

    @BeforeEach
    void setUp() {
        objectMapper = new ObjectMapper();
        objectMapper.setSerializationInclusion(JsonInclude.Include.NON_EMPTY);
    }

    @Test
    @DisplayName("Serializes a fully populated FieldErrorDto correctly using builder")
    void shouldSerializeFullyPopulatedDto() throws Exception {
        FieldErrorDto dto = FieldErrorDto.builder()
                .objectName("challengeDto")
                .field("title")
                .message("The title cannot be empty")
                .build();

        String json = objectMapper.writeValueAsString(dto);

        assertThat(json).contains("\"objectName\":\"challengeDto\"")
                .contains("\"field\":\"title\"")
                .contains("\"message\":\"The title cannot be empty\"")
                .startsWith("{").endsWith("}");
    }

    @Test
    @DisplayName("Does not serialize null fields when using @JsonInclude.NON_EMPTY with builder")
    void shouldOmitNullFieldsInJson() throws Exception {
        FieldErrorDto dto = FieldErrorDto.builder()
                .field("difficulty")
                .build();  // objectName and message are null

        String json = objectMapper.writeValueAsString(dto);

        assertThat(json).contains("\"field\":\"difficulty\"")
                .doesNotContain("objectName")
                .doesNotContain("message");
    }

}


// Node: setSerializationInclusion
// Node: shouldSerializeFullyPopulatedDto
// Node: endsWith
// Node: shouldOmitNullFieldsInJson
// Node: doesNotContain
// Node: timestamp
package com.itachallenge.errorcore.exceptionhandler;

import com.fasterxml.jackson.databind.exc.InvalidFormatException;
import com.itachallenge.errorcore.builder.ErrorResponseBuilder;
import com.itachallenge.errorcore.dto.APIErrorResponse;
import com.itachallenge.errorcore.exception.ApiCustomErrorInfo;
import com.itachallenge.errorcore.exception.BaseApiException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.ConstraintViolationException;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.HttpInputMessage;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.mock.http.MockHttpInputMessage;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.web.server.ServerWebInputException;

import java.util.Set;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class GlobalExceptionHandlerUnitTest {

    @Mock
    private ErrorResponseBuilder builder;

    @Mock
    private HttpServletRequest request;

    @InjectMocks
    private GlobalExceptionHandler handler;

    private final APIErrorResponse dummyResponse = APIErrorResponse.builder()
            .status(400)
            .error("Bad Request")
            .message("dummy")
            .build();


    @Test
    void handleAny_shouldReturnInternalServerError() {
        when(builder.buildError(any(Exception.class),eq(request)))
                .thenReturn(dummyResponse);

        ResponseEntity<APIErrorResponse> response = handler.handleAny(new Exception("boom"), request);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.INTERNAL_SERVER_ERROR);
        verify(builder).buildError(any(Exception.class), eq(request));
    }

    @Test
    void handleIllegalArgument_shouldReturnBadRequest() {
        when(builder.buildError(any(IllegalArgumentException.class), eq(request)))
                .thenReturn(dummyResponse);

        ResponseEntity<APIErrorResponse> response = handler.handleIllegalArgument(
                new IllegalArgumentException("invalid input"), request);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        verify(builder).buildError(any(IllegalArgumentException.class), eq(request));
    }

    @Test
    void handleValidationExceptions_shouldDelegateToBuilder() {
        ConstraintViolationException ex = new ConstraintViolationException(Set.of());
        when(builder.buildConstraintViolationErrorResponse(ex, request)).thenReturn(dummyResponse);

        ResponseEntity<APIErrorResponse> response = handler.handleValidationExceptions(ex, request);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        verify(builder).buildConstraintViolationErrorResponse(ex, request);
    }

    @Test
    void handleTypeMismatchException_shouldDelegateToBuilder() {
        MethodArgumentTypeMismatchException ex = mock(MethodArgumentTypeMismatchException.class);
        when(builder.buildTypeMismatchErrorResponse(ex, request)).thenReturn(dummyResponse);

        ResponseEntity<APIErrorResponse> response = handler.handleTypeMismatchException(ex, request);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        verify(builder).buildTypeMismatchErrorResponse(ex, request);
    }

    @Test
    void handleMethodArgumentNotValidException_shouldDelegateToBuilder() {
        MethodArgumentNotValidException ex = mock(MethodArgumentNotValidException.class);
        when(builder.buildArgumentNotValidErrorResponse(ex, request)).thenReturn(dummyResponse);

        ResponseEntity<APIErrorResponse> response = handler.handleMethodArgumentNotValidException(ex, request);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        verify(builder).buildArgumentNotValidErrorResponse(ex, request);
    }

    @Test
    void handleResponseStatusException_shouldUseStatusFromException() {
        ResponseStatusException ex = new ResponseStatusException(HttpStatus.NOT_FOUND, "Not found");
        when(builder.buildStatusErrorResponse(ex, request)).thenReturn(dummyResponse);

        ResponseEntity<APIErrorResponse> response = handler.handleResponseStatusException(ex, request);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.NOT_FOUND);
        verify(builder).buildStatusErrorResponse(ex, request);
    }

    @Test
    void handleInvalidFormat_shouldReturnBadRequestAndDelegateToBuilder() {
        InvalidFormatException ex = mock(InvalidFormatException.class);
        when(builder.buildError(ex, request))
                .thenReturn(dummyResponse);

        ResponseEntity<APIErrorResponse> response = handler.handleInvalidFormat(ex, request);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        assertThat(response.getBody()).isEqualTo(dummyResponse);
        verify(builder).buildError(ex, request);
    }

    @Test
    void handleWebFluxBindingErrors_withInvalidFormatCause_shouldDelegateToHandleInvalidFormat() {
        InvalidFormatException rootCause = mock(InvalidFormatException.class);
        HttpInputMessage mockInput = new MockHttpInputMessage("{}".getBytes());
        HttpMessageNotReadableException ex =
                new HttpMessageNotReadableException("invalid", rootCause, mockInput);
        when(builder.buildError(rootCause, request))
                .thenReturn(dummyResponse);

        ResponseEntity<APIErrorResponse> response = handler.handleWebFluxBindingErrors(ex, request);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        verify(builder).buildError(rootCause, request);
    }

    @Test
    void handleWebFluxBindingErrors_withoutInvalidFormatCause_shouldReturnGenericBadRequest() {
        ServerWebInputException ex = new ServerWebInputException("Bad JSON");
        when(builder.buildError(ex, request))
                .thenReturn(dummyResponse);
        ResponseEntity<APIErrorResponse> response = handler.handleWebFluxBindingErrors(ex, request);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        verify(builder).buildError(ex, request);
    }
    @Test
    void handleCustomError_shouldDelegateAndToCustomBuildAndReturnExceptionStatusCode(){

        class GenericNotFoundException extends BaseApiException {
            GenericNotFoundException(String arg){
                super(arg, ApiCustomErrorInfo.of(HttpStatus.NOT_FOUND,"error.notFound",new Object[]{arg}));
            }
        }
        GenericNotFoundException ex = new GenericNotFoundException("GenericNotFound");
        when (builder.buildCustomExceptionError(ex,request))
                .thenReturn(dummyResponse);

        ResponseEntity<APIErrorResponse> response = handler.handleApiCustomException(ex, request);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.NOT_FOUND);
        verify(builder).buildCustomExceptionError(ex,request);
    }
}


// Node: handleAny_shouldReturnInternalServerError
// Node: handleIllegalArgument_shouldReturnBadRequest
// Node: handleValidationExceptions_shouldDelegateToBuilder
// Node: handleTypeMismatchException_shouldDelegateToBuilder
// Node: handleMethodArgumentNotValidException_shouldDelegateToBuilder
// Node: handleResponseStatusException_shouldUseStatusFromException
// Node: handleInvalidFormat_shouldReturnBadRequestAndDelegateToBuilder
// Node: handleWebFluxBindingErrors_withInvalidFormatCause_shouldDelegateToHandleInvalidFormat
// Node: MockHttpInputMessage
// Node: getBytes
// Node: HttpMessageNotReadableException
// Node: handleWebFluxBindingErrors_withoutInvalidFormatCause_shouldReturnGenericBadRequest
// Node: ServerWebInputException
// Node: handleCustomError_shouldDelegateAndToCustomBuildAndReturnExceptionStatusCode
package com.itachallenge.errorcore.integrationTest;

import com.fasterxml.jackson.databind.exc.InvalidFormatException;
import com.itachallenge.errorcore.builder.ErrorResponseBuilder;
import com.itachallenge.errorcore.config.ErrorHandlingConfig;
import com.itachallenge.errorcore.dto.APIErrorResponse;
import com.itachallenge.errorcore.exception.ApiCustomErrorInfo;
import com.itachallenge.errorcore.exception.BaseApiException;
import com.itachallenge.errorcore.exceptionhandler.GlobalExceptionHandler;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.ConstraintViolation;
import jakarta.validation.ConstraintViolationException;
import jakarta.validation.Path;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.MessageSource;
import org.springframework.core.MethodParameter;
import org.springframework.core.codec.DecodingException;
import org.springframework.http.HttpInputMessage;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.junit.jupiter.SpringExtension;
import org.springframework.validation.BeanPropertyBindingResult;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;
import org.springframework.web.server.ResponseStatusException;

import java.lang.reflect.Method;
import java.util.Set;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

@ExtendWith(SpringExtension.class)
@ContextConfiguration(classes = { ErrorHandlingConfig.class })
class ErrorCoreIntegrationTest {

    @Autowired
    private MessageSource messageSource;

    @Autowired
    private ErrorResponseBuilder errorResponseBuilder;

    @Autowired
    private GlobalExceptionHandler handler;

    private HttpServletRequest request;

    @BeforeEach
    void setup() {
        request = mock(HttpServletRequest.class);
        when(request.getRequestURI()).thenReturn("/api/test");
    }

    // --- Dummy Controller & DTO for MethodParameter simulation ---
    static class EmptyController {
        public void handle(EmptyDto dto) {
            /* the method is just for testing -  hence its emptyness*/
        }
    }

    static class EmptyDto {
        @SuppressWarnings("unused")
        private String name;
    }

    @Test
    void handleAny_shouldReturnInternalServerError() {
        Exception ex = new Exception("Unexpected error");
        ResponseEntity<APIErrorResponse> response = handler.handleAny(ex, request);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.INTERNAL_SERVER_ERROR);
        assertThat(response.getBody()).isNotNull();
        assertThat(response.getBody().getStatus()).isEqualTo(500);
    }

    @Test
    void handleApiCustomException_shouldReturnCustomStatusAndText() {

        BaseApiException ex = mock(BaseApiException.class);
        when(ex.getMessage()).thenReturn("status.exception.401");
        when(ex.getInfo()).thenReturn(ApiCustomErrorInfo.of(HttpStatus.FORBIDDEN,"status.exception.401",new Object[]{}));
        ResponseEntity<APIErrorResponse> response = handler.handleApiCustomException(ex, request);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.FORBIDDEN);
        assertThat(response.getBody()).isNotNull();
        assertThat(response.getBody().getMessage()).isEqualTo("You are not authorized to perform this action.");
    }

    @Test
    void handleIllegalArgument_shouldReturnBadRequest() {
        IllegalArgumentException ex = new IllegalArgumentException("Invalid input");

        ResponseEntity<APIErrorResponse> response = handler.handleIllegalArgument(ex, request);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        assertThat(response.getBody()).isNotNull();
        assertThat(response.getBody().getMessage()).isEqualTo("Illegal argument in request.");
    }

    @Test
    void handleValidationExceptions_shouldReturnBadRequest_withSingleViolation() {
        // Given
        Path mockPath = mock(Path.class);
        when(mockPath.toString()).thenReturn("testField");

        ConstraintViolation<EmptyDto> violation = mock(ConstraintViolation.class);
        when(violation.getMessage()).thenReturn("must not be null");
        when(violation.getPropertyPath()).thenReturn(mockPath);
        when(violation.getRootBeanClass()).thenReturn(EmptyDto.class);

        Set<ConstraintViolation<?>> violations = Set.of(violation);
        ConstraintViolationException ex = new ConstraintViolationException("Validation failed", violations);

        // When
        ResponseEntity<APIErrorResponse> response = handler.handleValidationExceptions(ex, request);

        // Then
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        assertThat(response.getBody()).isNotNull();
        assertThat(response.getBody().getMessage()).contains("One or more request parameters failed validation.");
        assertThat(response.getBody().getErrors().getFirst().getObjectName()).isEqualTo("EmptyDto");
        assertThat(response.getBody().getErrors().getFirst().getMessage()).isEqualTo("Validation failed for parameter 'testField': must not be null");
    }

    @Test
    void handleTypeMismatch_shouldReturnBadRequest() throws NoSuchMethodException {
        // Given: we need a MethodParameter for a method argument of type Integer
        Method method = EmptyController.class.getDeclaredMethod("handle", EmptyDto.class);
        MethodParameter parameter = new MethodParameter(method, 0);

        MethodArgumentTypeMismatchException ex =
                new MethodArgumentTypeMismatchException("abc", EmptyDto.class, "dto", parameter, new IllegalArgumentException());

        // When
        ResponseEntity<APIErrorResponse> response = handler.handleTypeMismatchException(ex, request);

        // Then
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        assertThat(response.getBody()).isNotNull();
        assertThat(response.getBody().getMessage()).contains("Parameter 'dto' has invalid value 'abc'. Expected type: EmptyDto");
    }

    @Test
    void handleMethodArgumentNotValid_shouldReturnBadRequest() throws NoSuchMethodException {
        // Fake method parameter
        Method method = EmptyController.class.getDeclaredMethod("handle", EmptyDto.class);
        MethodParameter param = new MethodParameter(method, 0);

        // Simulate validation error
        EmptyDto dto = new EmptyDto();
        BeanPropertyBindingResult bindingResult = new BeanPropertyBindingResult(dto, "dummyDto");
        bindingResult.addError(new FieldError("emptyDto", "name", dto, false,
                new String[]{"validation.bad_request"}, null, null));

        MethodArgumentNotValidException ex = new MethodArgumentNotValidException(param, bindingResult);

        ResponseEntity<APIErrorResponse> response = handler.handleMethodArgumentNotValidException(ex, request);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        assertThat(response.getBody()).isNotNull();
        assertThat(response.getBody().getErrors()).hasSize(1);
        assertThat(response.getBody().getErrors().getFirst().getMessage()).isEqualTo("Invalid or malformed request.");
    }

    @Test
    void handleResponseStatusException_shouldReturnStatusFromException() {
        ResponseStatusException ex = new ResponseStatusException(HttpStatus.NOT_FOUND, "Resource not found");

        ResponseEntity<APIErrorResponse> response = handler.handleResponseStatusException(ex, request);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.NOT_FOUND);
        assertThat(response.getBody()).isNotNull();
        assertThat(response.getBody().getMessage()).isEqualTo("The requested resource could not be found.");
    }

    @Test
    void handleInvalidFormat_shouldReturnBadRequest() {
        InvalidFormatException ex = new InvalidFormatException(null, "Bad format", "123", Integer.class);

        ResponseEntity<APIErrorResponse> response = handler.handleInvalidFormat(ex, request);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        assertThat(response.getBody()).isNotNull();
        assertThat(response.getBody().getMessage()).isEqualTo("Invalid or malformed request.");
    }

    @Test
    void handleWebFluxBindingErrors_shouldReturnBadRequest() {
        DecodingException ex = new DecodingException("Unreadable message");
        ResponseEntity<APIErrorResponse> response = handler.handleWebFluxBindingErrors(ex, request);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        assertThat(response.getBody()).isNotNull();
        assertThat(response.getBody().getMessage()).isEqualTo("Invalid or malformed request.");
    }

    @Test
    void handleWebFluxBindingErrors_shouldHandleNestedInvalidFormat() {
        HttpInputMessage message = mock(HttpInputMessage.class);
        InvalidFormatException root = new InvalidFormatException(null, "Invalid format", "abc", Integer.class);
        HttpMessageNotReadableException ex = new HttpMessageNotReadableException("Outer", root,message);

        ResponseEntity<APIErrorResponse> response = handler.handleWebFluxBindingErrors(ex, request);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        assertThat(response.getBody()).isNotNull();
        assertThat(response.getBody().getMessage()).isEqualTo("Invalid or malformed request.");
    }
}


// Node: handleApiCustomException_shouldReturnCustomStatusAndText
// Node: handleValidationExceptions_shouldReturnBadRequest_withSingleViolation
// Node: handleTypeMismatch_shouldReturnBadRequest
// Node: handleMethodArgumentNotValid_shouldReturnBadRequest
// Node: EmptyDto
// Node: addError
// Node: FieldError
// Node: handleResponseStatusException_shouldReturnStatusFromException
// Node: handleInvalidFormat_shouldReturnBadRequest
// Node: InvalidFormatException
// Node: handleWebFluxBindingErrors_shouldReturnBadRequest
// Node: handleWebFluxBindingErrors_shouldHandleNestedInvalidFormat
package com.itachallenge.user.exception;

public class UsernameAlreadyExistsException extends RuntimeException {
    public UsernameAlreadyExistsException(String username) {
        super("The username '" + username + "' is already registered.");
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/exception/UsernameAlreadyExistsException.java:UsernameAlreadyExistsException.<init>
// Node: UsernameAlreadyExistsException
package com.itachallenge.user.exception;

public class DatabaseException extends RuntimeException {

    public DatabaseException(String message) {
        super(message);
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/exception/DatabaseException.java:DatabaseException.<init>
// Node: DatabaseException
package com.itachallenge.user.exception;

import com.itachallenge.githubcore.exception.GithubUnavailableException;
import com.itachallenge.user.dto.APIErrorResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;

import jakarta.validation.ConstraintViolationException;

import java.time.Instant;
import java.util.HashMap;
import java.util.Map;

@Slf4j
@RestControllerAdvice
public class UserGlobalExceptionHandler {

    @ExceptionHandler(Exception.class)
    public ResponseEntity<String> handleAny(Exception e) {
        log.error("Unexpected error happened: {}", e.getMessage());
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("Unexpected error happened.");
    }

    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<String> handleIllegalArgument(IllegalArgumentException e) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(e.getMessage());
    }

    @ExceptionHandler(ConstraintViolationException.class)
    public ResponseEntity<String> handleValidationExceptions(ConstraintViolationException ex) {
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(ex.getMessage());
    }

    @ExceptionHandler(MethodArgumentTypeMismatchException.class)
    public ResponseEntity<String> handleTypeMismatchException(MethodArgumentTypeMismatchException ex) {
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body("Invalid parameter format.");
    }

    @ExceptionHandler(BadRequestException.class)
    public ResponseEntity<String> handleBadRequestException(BadRequestException e) {
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(e.getMessage());
    }

    @ExceptionHandler(BadUUIDException.class)
    public ResponseEntity<String> handleBadUUIDException(BadUUIDException e) {
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body("The provided IDs are not valid.");
    }

    @ExceptionHandler(DatabaseException.class)
    public ResponseEntity<String> handleDatabaseException(DatabaseException e) {
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("Database error: " + e.getMessage());
    }

    @ExceptionHandler(NotFoundException.class)
    public ResponseEntity<String> handleNotFoundException(NotFoundException e) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(e.getMessage());
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Map<String, String>> handleMethodArgumentNotValidException(MethodArgumentNotValidException e){
        Map<String, String> errors = new HashMap<>();
        e.getBindingResult().getFieldErrors().forEach(error ->
                errors.put(error.getField(), error.getDefaultMessage())
        );
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(errors);
    }

    @ExceptionHandler(UnmodificableSolutionException.class)
    public ResponseEntity<String> handleUnmodifiableSolutionException(UnmodificableSolutionException e) {
        return ResponseEntity.status(HttpStatus.CONFLICT).body(e.getMessage());
    }

    @ExceptionHandler(InternalServerErrorException.class)
    public ResponseEntity<String> handleInternalServerErrorException(InternalServerErrorException e) {
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(e.getMessage());
    }

    @ExceptionHandler(UsernameAlreadyExistsException.class)
    public ResponseEntity<String> handleUsernameAlreadyExistsException(UsernameAlreadyExistsException e) {
        return ResponseEntity.status(HttpStatus.CONFLICT).body(e.getMessage());
    }

    @ExceptionHandler(GithubUnavailableException.class)
    public ResponseEntity<APIErrorResponse> handleGithubUnavailable(GithubUnavailableException ex) {
        HttpStatus status;
        String securedMessage;

        log.error("GithubUnavailableException occurred: {}", ex.getMessage(), ex);

        if (ex.getCause() instanceof java.net.SocketTimeoutException) {
            status = HttpStatus.GATEWAY_TIMEOUT;
            securedMessage = "The external GitHub service timed out.";
        } else if (ex.getCause() instanceof java.net.ConnectException) {
            status = HttpStatus.SERVICE_UNAVAILABLE;
            securedMessage = "The external GitHub service is currently unavailable.";
        } else {
            status = HttpStatus.SERVICE_UNAVAILABLE;
            securedMessage = "An external service error occurred.";
        }

        return ResponseEntity.status(status).body(
                new APIErrorResponse("External Service Error", securedMessage, Instant.now())
        );
    }
}

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/exception/UserGlobalExceptionHandler.java:UserGlobalExceptionHandler.<init>
// Node: handleBadRequestException
// Node: handleBadUUIDException
// Node: handleDatabaseException
// Node: handleNotFoundException
// Node: getDefaultMessage
// Node: handleUnmodifiableSolutionException
// Node: handleInternalServerErrorException
// Node: handleUsernameAlreadyExistsException
// Node: handleGithubUnavailable
// Node: APIErrorResponse
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



// Node: testHandleAny
// Node: assertTrue
// Node: requireNonNull
// Node: testHandleIllegalArgument
// Node: testHandleValidationExceptions
// Node: testHandleTypeMismatchException
// Node: testHandleBadRequestException
// Node: testHandleDatabaseException
// Node: testHandleNotFoundException
// Node: testHandleUnmodifiableSolutionException
// Node: testHandleUsernameAlreadyExistsException
// Node: handleGithubUnavailable_shouldReturn503
// Node: ConnectException
// Node: handleGithubUnavailable_shouldReturn504
// Node: SocketTimeoutException
// Node: handleGithubUnavailable_shouldReturn503ForOtherCauses
// Node: causes
package com.itachallenge.user.document;

import com.itachallenge.user.document.enums.Role;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

import java.util.*;

class UserDocumentTest {

    private UUID uuid;
    private String username;
    private Role role;
    private UserDocument userDocument;
    private Integer points;

    @BeforeEach
    void setUp() {
        uuid = UUID.randomUUID();
        username = "testUser";
        role = Role.ADMIN;
        points = 0;
        userDocument = UserDocument.builder()
                .uuid(uuid)
                .username(username)
                .role(role)
                .points(0)
                .build();
    }

    @Test
    void userDocumentCreation() {
        assertNotNull(userDocument);
        assertEquals(uuid, userDocument.getUuid());
        assertEquals(username, userDocument.getUsername());
        assertEquals(role, userDocument.getRole());
        assertEquals(points, userDocument.getPoints());
    }

    @Test
    void settersAndGetters() {
        UUID newUuid = UUID.randomUUID();
        String newUsername = "newUser";
        Role newRole = Role.USER;
        Integer newPoints = 0;

        userDocument.setUuid(newUuid);
        userDocument.setUsername(newUsername);
        userDocument.setRole(newRole);
        userDocument.setPoints(newPoints);

        assertEquals(newUuid, userDocument.getUuid());
        assertEquals(newUsername, userDocument.getUsername());
        assertEquals(newRole, userDocument.getRole());
        assertEquals(newPoints, userDocument.getPoints());
    }

    @Test
    void builderPattern() {
        UserDocument user = UserDocument.builder()
                .uuid(uuid)
                .username(username)
                .role(role)
                .points(points)
                .build();

        assertNotNull(user);
        assertEquals(uuid, user.getUuid());
        assertEquals(username, user.getUsername());
        assertEquals(role, user.getRole());
        assertEquals(points, user.getPoints());
    }

    @Test
    void noArgsConstructor() {
        UserDocument emptyUser = new UserDocument();
        assertNotNull(emptyUser);
        assertNull(emptyUser.getUuid());
        assertNull(emptyUser.getUsername());
        assertNull(emptyUser.getRole());
        assertEquals(0, emptyUser.getPoints());
    }

    @Test
    void allArgsConstructor() {
        UserDocument user = new UserDocument(uuid, username, role, points);
        assertNotNull(user);
        assertEquals(uuid, user.getUuid());
        assertEquals(username, user.getUsername());
        assertEquals(role, user.getRole());
        assertEquals(points, user.getPoints());
    }

    @Test
    void equalsAndHashCode() {
        UserDocument user1 = new UserDocument(uuid, username, role, points);
        UserDocument user2 = new UserDocument(uuid, username, role, points);

        assertEquals(user1, user2);
        assertEquals(user1.hashCode(), user2.hashCode());

        user2.setUsername("anotherUser");
        assertNotEquals(user1, user2);
    }

    @Test
    void equalsWithSameObject() {
        assertEquals(userDocument, userDocument);
    }

    @Test
    void equalsWithSameHashCode() {
        assertEquals(userDocument.hashCode(), userDocument.hashCode());
    }

    @Test
    void equalsAndHashCodeWithDifferentUUIDs() {
        UserDocument differentUser = new UserDocument(UUID.randomUUID(), username, role, points);

        assertNotEquals(userDocument, differentUser);
        assertNotEquals(userDocument.hashCode(), differentUser.hashCode());
    }

    @Test
    void equalsAndHashCodeWithDifferentUsernames() {
        UserDocument sameUuidDifferentUsername = new UserDocument(uuid, "differentUser", Role.USER, points);

        assertNotEquals(userDocument, sameUuidDifferentUsername);
        assertNotEquals(userDocument.hashCode(), sameUuidDifferentUsername.hashCode());
    }

    @Test
    void equalsAndHashCodeWithNullFields() {
        UserDocument userWithNullUuid = new UserDocument(null, username, role, points);
        UserDocument userWithNullUsername = new UserDocument(uuid, null, role, points);
        UserDocument userWithNullRole = new UserDocument(uuid, username, null, points);
        UserDocument userWithNullPoints = new UserDocument(uuid, username, role, 0);
        UserDocument completelyNullUser = new UserDocument(null, null, null, 0);

        assertNotEquals(userDocument, userWithNullUuid);
        assertNotEquals(userDocument, userWithNullUsername);
        assertNotEquals(userDocument, userWithNullRole);
        assertEquals(userDocument, userWithNullPoints);
        assertNotEquals(userDocument, completelyNullUser);

        assertNotEquals(userDocument.hashCode(), userWithNullUuid.hashCode());
        assertNotEquals(userDocument.hashCode(), userWithNullUsername.hashCode());
        assertNotEquals(userDocument.hashCode(), userWithNullRole.hashCode());
        assertEquals(userDocument.hashCode(), userWithNullPoints.hashCode());
        assertNotEquals(userDocument.hashCode(), completelyNullUser.hashCode());
    }

    @Test
    void equalsWithDifferentClass() {
        Object otherObject = new Object();
        assertNotEquals(userDocument, otherObject);
    }

    @Test
    void equalsWithNull() {
        assertNotEquals(null, userDocument);
    }

    @Test
    void equalsConsistencyTest() {
        UserDocument user1 = new UserDocument(uuid, username, role, points);
        UserDocument user2 = new UserDocument(uuid, username, role, points);

        assertEquals(user1, user2);
        assertEquals(user1, user2); // Repeated check for consistency
    }

    @Test
    void hashCodeConsistencyTest() {
        int initialHashCode = userDocument.hashCode();
        assertEquals(initialHashCode, userDocument.hashCode());
    }

    @Test
    void equalsTransitivityTest() {
        UserDocument user1 = new UserDocument(uuid, username, role, points);
        UserDocument user2 = new UserDocument(uuid, username, role, points);
        UserDocument user3 = new UserDocument(uuid, username, role, points);

        assertEquals(user1, user2);
        assertEquals(user2, user3);
        assertEquals(user1, user3);
    }

    @Test
    void equalsSymmetryTest() {
        UserDocument user1 = new UserDocument(uuid, username, role, points);
        UserDocument user2 = new UserDocument(uuid, username, role, points);

        assertEquals(user1, user2);
        assertEquals(user2, user1);
    }

    @Test
    void hashCodeEqualityForEqualObjects() {
        UserDocument user1 = new UserDocument(uuid, username, role, points);
        UserDocument user2 = new UserDocument(uuid, username, role, points);

        assertEquals(user1.hashCode(), user2.hashCode());
    }

    @Test
    void hashCodeDifferenceForNonEqualObjects() {
        UserDocument user1 = new UserDocument(UUID.randomUUID(), "user1", Role.ADMIN, points);
        UserDocument user2 = new UserDocument(UUID.randomUUID(), "user2", Role.ADMIN, points);

        assertNotEquals(user1.hashCode(), user2.hashCode());
    }

    @Test
    void equalsWithNullAttributes() {
        UserDocument user1 = new UserDocument(null, null, null, 0);
        UserDocument user2 = new UserDocument(null, null, null, 0);

        assertEquals(user1, user2);
        assertEquals(user1.hashCode(), user2.hashCode());
    }

    @Test
    void equalsWithOneNullUuid() {
        UserDocument user1 = new UserDocument(uuid, username, role, points);
        UserDocument user2 = new UserDocument(null, username, role, points);

        assertNotEquals(user1, user2);
        assertNotEquals(user1.hashCode(), user2.hashCode());
    }

    @Test
    void equalsWithOneNullUsername() {
        UserDocument user1 = new UserDocument(uuid, username, role, points);
        UserDocument user2 = new UserDocument(uuid, null, role, points);

        assertNotEquals(user1, user2);
        assertNotEquals(user1.hashCode(), user2.hashCode());
    }

    @Test
    void equalsWithOneNullRole() {
        UserDocument user1 = new UserDocument(uuid, username, role, points);
        UserDocument user2 = new UserDocument(uuid, username, null, points);

        assertNotEquals(user1, user2);
        assertNotEquals(user1.hashCode(), user2.hashCode());
    }

    @Test
    void toStringHandlesNullValues() {
        UserDocument user = new UserDocument(null, null, null, 0);
        String s = user.toString();

        assertNotNull(s);
        assertTrue(s.contains("UserDocument"));
    }


    @Test
    void builderHandlesNullValues() {
        UserDocument user = UserDocument.builder()
                .uuid(null)
                .username(null)
                .role(null)
                .points(0)
                .build();

        assertNotNull(user);
        assertNull(user.getUuid());
        assertNull(user.getUsername());
        assertNull(user.getRole());
        assertEquals(0, user.getPoints());
    }

    @Test
    void settersHandleNullValues() {
        userDocument.setUuid(null);
        userDocument.setUsername(null);
        userDocument.setRole(null);
        userDocument.setPoints(null);

        assertNull(userDocument.getUuid());
        assertNull(userDocument.getUsername());
        assertNull(userDocument.getRole());
        assertNull(userDocument.getPoints());
    }

    @Test
    void hashCodeDifferentForDifferentObjects() {
        UserDocument user1 = new UserDocument(UUID.randomUUID(), "UserA", Role.ADMIN, points);
        UserDocument user2 = new UserDocument(UUID.randomUUID(), "UserB", Role.ADMIN, points);

        assertNotEquals(user1.hashCode(), user2.hashCode());
    }

    @Test
    void builderHandlesOnlyUuid() {
        UserDocument user = UserDocument.builder()
                .uuid(uuid)
                .build();

        assertNotNull(user);
        assertEquals(uuid, user.getUuid());
        assertNull(user.getUsername());
        assertNull(user.getRole());
    }

    @Test
    void builderHandlesOnlyUsername() {
        UserDocument user = UserDocument.builder()
                .username(username)
                .build();

        assertNotNull(user);
        assertNull(user.getUuid());
        assertEquals(username, user.getUsername());
        assertNull(user.getRole());
    }

    @Test
    void builderHandlesOnlyRole() {
        UserDocument user = UserDocument.builder()
                .role(role)
                .build();

        assertNotNull(user);
        assertNull(user.getUuid());
        assertNull(user.getUsername());
        assertEquals(role, user.getRole());
    }


    @Test
    void builderHandlesOnlyPoints() {
        UserDocument user = UserDocument.builder()
                .points(points)
                .build();

        assertNotNull(user);
        assertNull(user.getUuid());
        assertNull(user.getUsername());
        assertNull(user.getRole());
        assertEquals(points, user.getPoints());
    }

    @Test
    void builderCreatesNewInstances() {
        UserDocument user1 = UserDocument.builder().uuid(uuid).username(username).role(role)
                .build();

        UserDocument user2 = UserDocument.builder().uuid(uuid).username(username).role(role)
                .build();

        assertNotSame(user1, user2);
        assertEquals(user1, user2);
    }

    @Test
    void builderWithoutParametersCreatesValidObject() {
        UserDocument user = UserDocument.builder().build();

        assertNotNull(user);
        assertNull(user.getUuid());
        assertNull(user.getUsername());
        assertNull(user.getRole());
    }

    @Test
    void modifyingBuiltObjectDoesNotAffectOriginalBuilder() {
        UserDocument.UserDocumentBuilder builder = UserDocument.builder().uuid(uuid).username(username).role(role);

        UserDocument user1 = builder.build();
        UserDocument user2 = builder.uuid(UUID.randomUUID()).username("newUser").role(Role.USER)
                .build();

        assertNotEquals(user1, user2);
        assertNotEquals(user1.getUuid(), user2.getUuid());
        assertNotEquals(user1.getUsername(), user2.getUsername());
        assertNotEquals(user1.getRole(), user2.getRole());
    }
}


// Node: toStringHandlesNullValues
package com.itachallenge.user.document.enums;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.exc.InvalidFormatException;
import com.fasterxml.jackson.databind.exc.ValueInstantiationException;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class SolutionActionTest {
    private final ObjectMapper mapper = new ObjectMapper();

    @Test
    void shouldDeserializeSaveIgnoringCase() throws Exception{
        String json = "\"SaVe\"";
        SolutionAction result = mapper.readValue(json, SolutionAction.class);

        assertEquals(SolutionAction.SAVE, result);
    }

    @Test
    void shouldDeserializeGiveUpIgnoringCase() throws Exception {
        String json = "\"GivE_uP\"";
        SolutionAction result = mapper.readValue(json, SolutionAction.class);

        assertEquals(SolutionAction.GIVE_UP, result);
    }

    @Test
    void shouldDeserializeSubmitWithSpaces() throws Exception {
        String json = "\"   submit   \"";
        SolutionAction result = mapper.readValue(json, SolutionAction.class);

        assertEquals(SolutionAction.SUBMIT, result);
    }

    @Test
    void shouldThrowExceptionForInvalidValue() {
        String json = "\"INVALID_VALUE\"";

        ValueInstantiationException ex = assertThrows(
                ValueInstantiationException.class,
                () -> mapper.readValue(json, SolutionAction.class)
        );


        assertNotNull(ex.getCause());
        assertInstanceOf(IllegalArgumentException.class, ex.getCause());
        assertTrue(ex.getCause().getMessage().contains("Action must be one of"));
    }

    @Test
    void shouldReturnNullWhenJsonNull() throws Exception{
        String json = "null";
        SolutionAction result = mapper.readValue(json, SolutionAction.class);

        assertNull(result);
    }
}


// Node: shouldThrowExceptionForInvalidValue
// Node: shouldReturnNullWhenJsonNull
package com.itachallenge.user.dto;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;
import static org.junit.jupiter.api.Assertions.assertTrue;

public class SolvedDtoTest {

    @Test
    void testNoArgsConstructorAndSetters() {
        SolvedDto dto = new SolvedDto();
        dto.setSolved(true);
        dto.setTimesSolved(5);

        assertTrue(dto.isSolved());
        assertEquals(5, dto.getTimesSolved());
    }

    @Test
    void testAllArgsConstructor() {
        SolvedDto dto = new SolvedDto(false, 3);

        assertFalse(dto.isSolved());
        assertEquals(3, dto.getTimesSolved());
    }

    @Test
    void testEqualsAndHashCode() {
        SolvedDto dto1 = new SolvedDto(true, 2);
        SolvedDto dto2 = new SolvedDto(true, 2);
        SolvedDto dto3 = new SolvedDto(false, 5);

        assertEquals(dto1, dto2);
        assertEquals(dto1.hashCode(), dto2.hashCode());
        assertNotEquals(dto1, dto3);
    }

    @Test
    void testToString() {
        SolvedDto dto = new SolvedDto(true, 7);
        String result = dto.toString();

        assertTrue(result.contains("isSolved=true"));
        assertTrue(result.contains("timesSolved=7"));
    }
}


// Node: testToString
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

// Node: testLombokGeneratedMethods
package com.itachallenge.user.dto;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.itachallenge.user.document.enums.ChallengeStatus;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Assertions.*;

class UserSolutionResponseDtoTest {

    private UserSolutionResponseDto userSolutionResponseDto;
    String userId = UUID.randomUUID().toString();
    String challengeId = UUID.randomUUID().toString();
    String languageId = UUID.randomUUID().toString();
    String solutionText = "This is my solution";
    String status = ChallengeStatus.IN_PROGRESS.name();
    UserSolutionResponseDto solutionScoreDto = new UserSolutionResponseDto();
    UserSolutionResponseDto dto1 = UserSolutionResponseDto.builder().build();

    @BeforeEach
    public void setUp() {
        userSolutionResponseDto = UserSolutionResponseDto.builder()
                .userId("validUserId")
                .challengeId("validChallengeId")
                .languageId("validLanguageId")
                .solutionText("Valid solution text")
                .build();
    }

    @Test
    void lombokGeneratedMethods_test() {
        assertThat(dto1).isNotNull();
        assertThat(dto1.getClass()).isEqualTo(UserSolutionResponseDto.class);
    }

    @Test
    void getterUserSolutionScoreDto_test() {
        assertNotNull(userSolutionResponseDto);
        assertEquals("validUserId", userSolutionResponseDto.getUserId());
        assertEquals("validChallengeId", userSolutionResponseDto.getChallengeId());
        assertEquals("validLanguageId", userSolutionResponseDto.getLanguageId());
        assertEquals("Valid solution text", userSolutionResponseDto.getSolutionText());
    }

    @Test
    void noArgsConstructor_GetterAndSetter_UserSolutionScoreDto_test(){
        solutionScoreDto.setUserId(userId);
        solutionScoreDto.setChallengeId(challengeId);
        solutionScoreDto.setLanguageId(languageId);
        solutionScoreDto.setSolutionText(solutionText);

        assertThat(solutionScoreDto.getUserId()).isEqualTo(userId);
        assertThat(solutionScoreDto.getChallengeId()).isEqualTo(challengeId);
        assertThat(solutionScoreDto.getLanguageId()).isEqualTo(languageId);
        assertThat(solutionScoreDto.getSolutionText()).isEqualTo(solutionText);
    }

    @Test
    void jsonSerialization_test() throws Exception{
        ObjectMapper mapper = new ObjectMapper();
        String json = mapper.writeValueAsString(userSolutionResponseDto);
        assertTrue(json.contains("\"uuid_user\":\"validUserId\""));
        assertTrue(json.contains("\"uuid_language\":\"validLanguageId\""));
        assertTrue(json.contains("\"uuid_challenge\":\"validChallengeId\""));
        assertTrue(json.contains("\"solution_text\":\"Valid solution text\""));
    }

    @Test
    void requiredArgsConstructor_userSolutionScoreDto_test(){
        UserSolutionResponseDto userSolutionResponseDto1 = new UserSolutionResponseDto(
                userId, challengeId, languageId, solutionText,status);
        assertThat(userSolutionResponseDto1.getUserId()).isEqualTo(userId);
        assertThat(userSolutionResponseDto1.getChallengeId()).isEqualTo(challengeId);
        assertThat(userSolutionResponseDto1.getLanguageId()).isEqualTo(languageId);
        assertThat(userSolutionResponseDto1.getSolutionText()).isEqualTo(solutionText);
        assertThat(userSolutionResponseDto1.getStatus()).isEqualTo(status);
    }

    @Test
    void jsonSerialization_includesStatusField_withEndedStatus() throws Exception {
        UserSolutionResponseDto dto = UserSolutionResponseDto.builder()
                .userId("validUserId")
                .challengeId("validChallengeId")
                .languageId("validLanguageId")
                .solutionText("Valid solution text")
                .status("SUBMITTED_COMPLETE")
                .build();

        ObjectMapper mapper = new ObjectMapper();
        String json = mapper.writeValueAsString(dto);

        assertTrue(json.contains("\"status\":\"SUBMITTED_COMPLETE\""));
    }

    @Test
    void jsonSerialization_includesStatusField_withInProgressStatus() throws Exception {
        UserSolutionResponseDto dto = UserSolutionResponseDto.builder()
                .userId("validUserId")
                .challengeId("validChallengeId")
                .languageId("validLanguageId")
                .solutionText("Valid solution text")
                .status("IN_PROGRESS")
                .build();

        ObjectMapper mapper = new ObjectMapper();
        String json = mapper.writeValueAsString(dto);

        assertTrue(json.contains("\"status\":\"IN_PROGRESS\""));
    }
}

// Node: lombokGeneratedMethods_test
package com.itachallenge.user.dto;

import org.junit.jupiter.api.Test;

import java.time.Instant;

import static org.junit.jupiter.api.Assertions.assertEquals;

class APIErrorResponseTest {

    @Test
    void testConstructorAndGetters() {
        Instant now = Instant.now();
        APIErrorResponse errorResponse = new APIErrorResponse("Some error", "Something went wrong", now);

        assertEquals("Some error", errorResponse.getError());
        assertEquals("Something went wrong", errorResponse.getMessage());
        assertEquals(now, errorResponse.getTimestamp());
    }

    @Test
    void testNoArgsConstructorAndSetters() {
        Instant now = Instant.now();
        APIErrorResponse errorResponse = new APIErrorResponse();
        errorResponse.setError("Another error");
        errorResponse.setMessage("Different message");
        errorResponse.setTimestamp(now);

        assertEquals("Another error", errorResponse.getError());
        assertEquals("Different message", errorResponse.getMessage());
        assertEquals(now, errorResponse.getTimestamp());
    }
}


// Node: testConstructorAndGetters
// Node: setError
// Node: setMessage
// Node: setTimestamp
package com.itachallenge.common.exception;

import com.fasterxml.jackson.databind.JsonMappingException.Reference;
import com.fasterxml.jackson.databind.exc.InvalidFormatException;
import com.itachallenge.challenge.dto.MessageDto;
import com.itachallenge.challenge.exception.*;
import com.itachallenge.common.exception.dto.ErrorResponseDto;
import com.itachallenge.common.exception.enums.ErrorCode;
import com.itachallenge.submission.exception.SubmissionNotFoundException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.ConstraintViolation;
import jakarta.validation.ConstraintViolationException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.server.ResponseStatusException;
import com.itachallenge.submission.exception.UnmodifiableSubmissionException;

import java.time.Instant;
import java.util.Arrays;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import java.util.stream.Collectors;

@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    @ExceptionHandler(ResponseStatusException.class)
    public ResponseEntity<MessageDto> handleResponseStatusException(ResponseStatusException ex) {
        HttpStatus statusCode = (HttpStatus) ex.getStatusCode();
        String errorMessage;
        Object[] detailMessageArguments = ex.getDetailMessageArguments();
        if (detailMessageArguments == null || detailMessageArguments.length == 0) {
            errorMessage = "Validation failed";
        } else {
            errorMessage = Arrays.stream(detailMessageArguments)
                    .skip(1)
                    .map(Object::toString)
                    .collect(Collectors.joining(", "));
            errorMessage = errorMessage.replace("[", "").replace("]", "");
        }
        MessageDto errorResponseMessage = new MessageDto(errorMessage);
        return ResponseEntity.status(statusCode).body(errorResponseMessage);
    }

    @ExceptionHandler(ConstraintViolationException.class)
    public ResponseEntity<MessageDto> handleConstraintViolation(ConstraintViolationException ex) {
        String constraintMessage = ex.getConstraintViolations()
                .stream().findFirst().map(ConstraintViolation::getMessage).orElse("Invalid value");
        return ResponseEntity.badRequest().body(new MessageDto(constraintMessage));
    }

    @ExceptionHandler(ChallengeNotFoundException.class)
    public ResponseEntity<?> handleChallengeNotFoundException(ChallengeNotFoundException ex,
                                                              HttpServletRequest request) {
        if (request.getMethod().equals(HttpMethod.GET.name())
                && request.getRequestURI()
                .startsWith("/itachallenge/api/v1/challenge/challenges/")
                && !request.getRequestURI().endsWith("/byFilter")
                && !request.getRequestURI().endsWith("/related")) {
            ErrorResponseDto error = ErrorResponseDto.builder()
                    .errorCode(ErrorCode.CHALLENGE_NOT_FOUND.name())
                    .message(ex.getMessage())
                    .timestamp(Instant.now().toString())
                    .path(request.getRequestURI())
                    .build();
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(error);
        }
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(new MessageDto(ex.getMessage()));
    }

    @ExceptionHandler(TagNotFoundException.class)
    public ResponseEntity<MessageDto> handleTagNotFoundException(TagNotFoundException ex) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(new MessageDto(ex.getMessage()));
    }

    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<MessageDto> handleResourceNotFoundException(ResourceNotFoundException ex) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(new MessageDto(ex.getMessage()));
    }

    @ExceptionHandler(SubmissionNotFoundException.class)
    public ResponseEntity<MessageDto> handleSubmissionNotFoundException(SubmissionNotFoundException ex) {
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(new MessageDto(ex.getMessage()));
    }

    @ExceptionHandler(LanguageNotFoundException.class)
    public ResponseEntity<MessageDto> handleLanguageNotFoundException(LanguageNotFoundException ex) {
        return ResponseEntity.badRequest().body(new MessageDto(ex.getMessage()));
    }

    @ExceptionHandler(NotFoundException.class)
    public ResponseEntity<MessageDto> handleNotFoundException(NotFoundException ex) {
        return ResponseEntity.ok().body(new MessageDto(ex.getMessage()));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<?> handleMethodArgumentNotValidException(MethodArgumentNotValidException ex,
                                                                   HttpServletRequest request) {
        if (request.getMethod().equals(HttpMethod.POST.name())
                && request.getRequestURI().equals("/itachallenge/api/v1/challenge/challenges")) {
            Map<String, Object> details = ex.getBindingResult()
                    .getFieldErrors()
                    .stream()
                    .collect(Collectors.toMap(
                            FieldError::getField,
                            FieldError::getDefaultMessage,
                            (first, second) -> first
                    ));
            ErrorResponseDto error = ErrorResponseDto.builder()
                    .errorCode(ErrorCode.VALIDATION_ERROR.name())
                    .message("Validation failed")
                    .timestamp(Instant.now().toString())
                    .path(request.getRequestURI())
                    .details(details)
                    .build();
            return ResponseEntity.badRequest().body(error);
        }
        return ResponseEntity.badRequest().body(new MessageDto(ex.getMessage()));
    }

    @ExceptionHandler(BadUUIDException.class)
    public ResponseEntity<MessageDto> handleBadUUIDException(BadUUIDException ex) {
        return ResponseEntity.badRequest().body(new MessageDto(ex.getMessage()));
    }

    @ExceptionHandler(BadRequestException.class)
    public ResponseEntity<MessageDto> handleCustomBadRequestException(BadRequestException ex) {
        return ResponseEntity.badRequest().body(new MessageDto(ex.getMessage()));
    }

    @ExceptionHandler(InternalServerErrorException.class)
    public ResponseEntity<MessageDto> handleCustomInternalServerErrorException(InternalServerErrorException ex) {
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(new MessageDto(ex.getMessage()));
    }

    @ExceptionHandler
    public ResponseEntity<MessageDto> handleIllegalArgumentException(IllegalArgumentException e) {
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(new MessageDto(e.getMessage()));
    }

    @ExceptionHandler(InvalidFormatException.class)
    public ResponseEntity<?> handleInvalidFormat(InvalidFormatException ex,
                                                 HttpServletRequest request) {
        if (request.getMethod().equals(HttpMethod.POST.name())
                && request.getRequestURI().equals("/itachallenge/api/v1/challenge/challenges")) {
            Map<String, Object> details = Map.of(
                    "invalidValue", String.valueOf(ex.getValue())
            );
            ErrorResponseDto error = ErrorResponseDto.builder()
                    .errorCode(ErrorCode.VALIDATION_ERROR.name())
                    .message("Validation failed")
                    .timestamp(Instant.now().toString())
                    .path(request.getRequestURI())
                    .details(details)
                    .build();
            return ResponseEntity.badRequest().body(error);
        }
        return buildTagUuidError(ex)
                .orElseGet(() ->
                        ResponseEntity.badRequest().body(new MessageDto(ex.getOriginalMessage()))
                );
    }

    private Optional<ResponseEntity<MessageDto>> buildTagUuidError(InvalidFormatException ex) {
        if (UUID.class.equals(ex.getTargetType())) {
            String badValue = ex.getValue().toString();
            boolean fromTags = ex.getPath().stream()
                    .map(Reference::getFieldName)
                    .anyMatch("tags"::equals);
            if (fromTags) {
                MessageDto body = new MessageDto("invalid format UUID tag: " + badValue);
                return Optional.of(ResponseEntity
                        .badRequest()
                        .body(body));
            }
        }
        return Optional.empty();
    }

    @ExceptionHandler(UnmodifiableSubmissionException.class)
    public ResponseEntity<MessageDto> handleUnmodifiableSubmission(UnmodifiableSubmissionException ex) {
        return ResponseEntity.status(HttpStatus.CONFLICT).body(new MessageDto(ex.getMessage()));
    }

}

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/common/exception/GlobalExceptionHandler.java:GlobalExceptionHandler.<init>
// Node: getDetailMessageArguments
// Node: skip
// Node: MessageDto
// Node: handleConstraintViolation
// Node: handleChallengeNotFoundException
// Node: getMethod
// Node: errorCode
// Node: handleTagNotFoundException
// Node: handleResourceNotFoundException
// Node: handleSubmissionNotFoundException
// Node: handleLanguageNotFoundException
// Node: toMap
// Node: details
// Node: handleCustomBadRequestException
// Node: handleCustomInternalServerErrorException
// Node: handleIllegalArgumentException
// Node: buildTagUuidError
// Node: orElseGet
// Node: getOriginalMessage
// Node: getTargetType
// Node: handleUnmodifiableSubmission
package com.itachallenge.challenge.exception;

public class ResourceNotFoundException extends RuntimeException {
    public ResourceNotFoundException(String message) {
        super(message);
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/exception/ResourceNotFoundException.java:ResourceNotFoundException.<init>
// Node: ResourceNotFoundException
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


package com.itachallenge.challenge.service;

import io.jsonwebtoken.Claims;

public interface IChallengeJwtFacade {

    String getUserUuIdFromAuthenticationHeader(String authHeader);
    Claims extractAllClaims(String token);


}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/service/IChallengeJwtFacade.java:IChallengeJwtFacade.<init>
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


// Node: testHandleResponseStatusException
// Node: testHandleResponseStatusException_NullDetailMessageArguments
// Node: TestHandleMethodArgumentNotValidException
// Node: MockHttpServletRequest
// Node: setMethod
// Node: setRequestURI
// Node: notNullValue
// Node: TestHandleMethodArgumentNotValidException_Return_DefaultMessage
// Node: getCodes
// Node: testHandleChallengeNotFoundException
// Node: testHandleResourceNotFoundException
// Node: test_HandleBadUUIDException
// Node: testHandleLanguageNotFoundException
// Node: testHandleCustomInternalServerErrorException
// Node: testHandleTagNotFoundException
// Node: testHandleInvalidFormat_TagsField
// Node: prependPath
// Node: Reference
// Node: testHandleInvalidFormat_OtherFieldFallback
// Node: testHandleChallengeNotFound_GET_ReturnsErrorResponseDto
// Node: getErrorCode
// Node: testHandleMethodArgumentNotValid_POST_ReturnsErrorResponseDtoWithDetails
// Node: getDetails
// Node: testHandleInvalidFormat_PostChallenges_ReturnsErrorResponseDto
package com.itachallenge.common.exception.dto;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import java.util.Map;
import static org.assertj.core.api.Assertions.assertThat;

class ErrorResponseDtoTest {

    private final ObjectMapper objectMapper = new ObjectMapper();

    @Test
    void whenDetailsIsPresent_thenItIsSerialized() throws Exception {
        ErrorResponseDto dto = ErrorResponseDto.builder()
                .errorCode("VALIDATION_ERROR")
                .message("Validation failed")
                .timestamp("2026-02-08T12:00:00Z")
                .path("/api/v1/test")
                .details(Map.of("field", "error"))
                .build();

        String json = objectMapper.writeValueAsString(dto);

        assertThat(json).contains("\"details\"");
        assertThat(json).contains("\"field\":\"error\"");
    }

    @Test
    void whenDetailsIsNull_thenItIsNotSerialized() throws Exception {
        ErrorResponseDto dto = ErrorResponseDto.builder()
                .errorCode("VALIDATION_ERROR")
                .message("Validation failed")
                .timestamp("2026-02-08T12:00:00Z")
                .path("/api/v1/test")
                .build();

        String json = objectMapper.writeValueAsString(dto);

        assertThat(json).doesNotContain("details");
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/common/exception/dto/ErrorResponseDtoTest.java:ErrorResponseDtoTest.<init>
// Node: whenDetailsIsPresent_thenItIsSerialized
// Node: whenDetailsIsNull_thenItIsNotSerialized
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


// Node: languageImageShouldNotBeNullOrEmpty
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


package com.itachallenge.challenge.dto;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class SolvedDtoTest {

    @Test
    void testNoArgsConstructorAndSetters() {
        SolvedDto dto = new SolvedDto();
        dto.setSolved(true);
        dto.setTimesSolved(5);

        assertTrue(dto.isSolved());
        assertEquals(5, dto.getTimesSolved());
    }

    @Test
    void testAllArgsConstructor() {
        SolvedDto dto = new SolvedDto(false, 3);

        assertFalse(dto.isSolved());
        assertEquals(3, dto.getTimesSolved());
    }

    @Test
    void testEqualsAndHashCode() {
        SolvedDto dto1 = new SolvedDto(true, 2);
        SolvedDto dto2 = new SolvedDto(true, 2);
        SolvedDto dto3 = new SolvedDto(false, 5);

        assertEquals(dto1, dto2);
        assertEquals(dto1.hashCode(), dto2.hashCode());
        assertNotEquals(dto1, dto3);
    }

    @Test
    void testToString() {
        SolvedDto dto = new SolvedDto(true, 7);
        String result = dto.toString();

        assertTrue(result.contains("isSolved=true"));
        assertTrue(result.contains("timesSolved=7"));
    }
}


package com.itachallenge.challenge.dto;

import jakarta.validation.ConstraintViolation;
import jakarta.validation.Validation;
import jakarta.validation.Validator;
import jakarta.validation.ValidatorFactory;
import org.hibernate.validator.messageinterpolation.ResourceBundleMessageInterpolator;
import org.hibernate.validator.resourceloading.PlatformResourceBundleLocator;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.Locale;
import java.util.Set;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;

class SolutionDtoTest {

    private static Validator validator;

    @BeforeAll
    static void setupValidator() {
        // ✅ Force locale for predictable message interpolation
        Locale.setDefault(Locale.ENGLISH);

        // ✅ Create a Validator that explicitly loads messages.properties
        ValidatorFactory factory = Validation.byDefaultProvider()
                .configure()
                .messageInterpolator(
                        new ResourceBundleMessageInterpolator(
                                new PlatformResourceBundleLocator("messages")
                        )
                )
                .buildValidatorFactory();

        validator = factory.getValidator();
    }

    @Test
    @DisplayName("Should fail validation when solutionText is empty")
    void shouldFailWhenSolutionTextEmpty() {
        SolutionDto dto = new SolutionDto(
                UUID.randomUUID(),
                "", // invalid: empty
                UUID.randomUUID()
        );

        Set<ConstraintViolation<SolutionDto>> violations = validator.validate(dto);

        assertThat(violations).isNotEmpty()
                .anyMatch(v -> v.getMessage().equals("The solution text cannot be empty."));
    }

    @Test
    @DisplayName("Should fail when language or challenge UUIDs are invalid")
    void shouldFailForInvalidUUIDs() {
        // Simulate invalid UUIDs (null)
        SolutionDto dto = new SolutionDto(null, "some text", null);

        Set<ConstraintViolation<SolutionDto>> violations = validator.validate(dto);

        assertThat(violations).isNotEmpty()
                .anyMatch(v -> v.getMessage().equals("The language ID must be a valid UUID."))
                .anyMatch(v -> v.getMessage().equals("The challenge ID must be a valid UUID."));
    }

    @Test
    @DisplayName("Should pass validation for a valid SolutionDto")
    void shouldPassWhenValid() {
        SolutionDto dto = new SolutionDto(
                UUID.randomUUID(),
                "Valid solution text",
                UUID.randomUUID()
        );
        dto.setIdChallenge(UUID.randomUUID());

        Set<ConstraintViolation<SolutionDto>> violations = validator.validate(dto);

        assertThat(violations).isEmpty();
    }
}

// Node: shouldFailWhenSolutionTextEmpty
// Node: shouldFailForInvalidUUIDs
// Node: UUIDs
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

// Node: ExecutionTest
// Node: getInfoLogs
// Node: rollbackTest
package com.itachallenge.auth.exception;

import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.JwtException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.Map;

@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final String MESSAGE_KEY = "message";

    @ExceptionHandler(ExpiredJwtException.class)
    public ResponseEntity<Map<String, String>> handleExpiredJwt(ExpiredJwtException ex) {
        return ResponseEntity.ok(Map.of(MESSAGE_KEY, ex.getMessage()));
    }

    @ExceptionHandler(JwtException.class)
    public ResponseEntity<Map<String, String>> handleJwtException(JwtException ex) {
        return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                .body(Map.of(MESSAGE_KEY, ex.getMessage()));
    }

    @ExceptionHandler(InvalidRoleChangeRequestException.class)
    public ResponseEntity<Map<String, String>> handleInvalidRoleChange(InvalidRoleChangeRequestException ex) {
        return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                .body(Map.of(MESSAGE_KEY, ex.getMessage()));
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-auth/src/main/java/com/itachallenge/auth/exception/GlobalExceptionHandler.java:GlobalExceptionHandler.<init>
// Node: handleExpiredJwt
// Node: handleJwtException
// Node: handleInvalidRoleChange
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


package com.itachallenge.auth.service;

import com.itachallenge.jwtcore.service.IJwtService;
import io.jsonwebtoken.Claims;
import org.springframework.stereotype.Service;

@Service
public class AuthJwtFacade implements IAuthJwtFacade{

    private final IJwtService jwtService;

    public AuthJwtFacade(IJwtService jwtService) {
        this.jwtService = jwtService;
    }

    @Override
    public String generateToken(String username, String role, String uuid) {
        return jwtService.generateToken(username, role, uuid);
    }

    @Override
    public void validateToken(String token) {
        jwtService.validateToken(token);
    }

    @Override
    public Claims extractAllClaims(String token) {
        return jwtService.extractAllClaims(token);
    }

    @Override
    public String extractBearerToken(String authHeader) {
        return jwtService.extractBearerToken(authHeader);
    }
}


package com.itachallenge.auth.exception;

import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Header;
import io.jsonwebtoken.Claims;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class GlobalExceptionHandlerTest {

    private final GlobalExceptionHandler handler = new GlobalExceptionHandler();

    @Test
    void testHandleExpiredJwtException() {
        Header header = mock(Header.class);
        Claims claims = mock(Claims.class);
        String message = "Token expired during logout validation";
        ExpiredJwtException ex = new ExpiredJwtException(header, claims, message);

        ResponseEntity<Map<String, String>> response = handler.handleExpiredJwt(ex);

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals(message, response.getBody().get("message"));
    }

    @Test
    void testHandleJwtException() {
        String message = "Token is invalid or tampered";
        JwtException ex = new JwtException(message);

        ResponseEntity<Map<String, String>> response = handler.handleJwtException(ex);

        assertEquals(HttpStatus.UNAUTHORIZED, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals(message, response.getBody().get("message"));
    }

    @Test
    void handleInvalidRoleChange_ShouldReturnBadRequestWithMessage() {
        String message = "Invalid role.";
        InvalidRoleChangeRequestException exception = new InvalidRoleChangeRequestException(message);

        ResponseEntity<Map<String, String>> response = handler.handleInvalidRoleChange(exception);

        assertEquals(HttpStatus.BAD_REQUEST, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals(message, response.getBody().get("message"));
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-auth/src/test/java/com/itachallenge/auth/exception/GlobalExceptionHandlerTest.java:GlobalExceptionHandlerTest.<init>
// Node: testHandleExpiredJwtException
// Node: testHandleJwtException
// Node: handleInvalidRoleChange_ShouldReturnBadRequestWithMessage
//package com.itachallenge.auth.service;
//
//import com.itachallenge.auth.exception.InvalidRoleChangeRequestException;
//import io.jsonwebtoken.Claims;
//import io.jsonwebtoken.ExpiredJwtException;
//import io.jsonwebtoken.JwtException;
//import io.jsonwebtoken.Jwts;
//import io.jsonwebtoken.security.Keys;
//import org.junit.jupiter.api.BeforeEach;
//import org.junit.jupiter.api.Test;
//
//import java.util.Date;
//
//import static org.assertj.core.api.Assertions.assertThat;
//import static org.assertj.core.api.Assertions.assertThatThrownBy;
//
//class JwtServiceTest {
//
//    private JwtService jwtService;
//
//    // Clave en Base64, válida para HMAC-SHA con al menos 256 bits
//    private final String jwtSigningKey = "bXlTZWNyZXRTaWduaW5nS2V5V2hpY2hJc1ZlcnlTZWN1cmVBbmRub2JvZHlDb3VsZEd1ZXNz";
//    private final long minutesTillExpiration = 10L;
//
//    @BeforeEach
//    void setUp() {
//        jwtService = new JwtService(jwtSigningKey, minutesTillExpiration);
//    }
//
//    @Test
//    void generateToken_ShouldReturnValidJwt() {
//        String username = "testUser";
//        String role = "ADMIN";
//        String uuid = "uuid";
//
//        String token = jwtService.generateToken(username, role, uuid);
//
//        assertThat(token).isNotNull().isNotEmpty();
//
//        Claims claims = Jwts.parser()
//                .verifyWith(Keys.hmacShaKeyFor(io.jsonwebtoken.io.Decoders.BASE64.decode(jwtSigningKey)))
//                .build()
//                .parseSignedClaims(token)
//                .getPayload();
//
//        assertThat(claims.getSubject()).isEqualTo(username);
//        assertThat(claims.get("role", String.class)).isEqualTo(role);
//        assertThat(claims.get("uuid", String.class)).isEqualTo(uuid);
//        assertThat(claims.getExpiration()).isAfter(new Date());
//    }
//
//    @Test
//    void generateToken_ShouldHaveCorrectExpirationTime() {
//        String username = "testUser";
//        String role = "USER";
//        String uuid = "uuid";
//        long expectedExpirationMillis = System.currentTimeMillis() + (minutesTillExpiration * 60000);
//
//        String token = jwtService.generateToken(username, role, uuid);
//
//        Claims claims = Jwts.parser()
//                .verifyWith(Keys.hmacShaKeyFor(io.jsonwebtoken.io.Decoders.BASE64.decode(jwtSigningKey)))
//                .build()
//                .parseSignedClaims(token)
//                .getPayload();
//
//        long actualExpirationMillis = claims.getExpiration().getTime();
//        assertThat(actualExpirationMillis)
//                .isBetween(expectedExpirationMillis - 5000, expectedExpirationMillis + 5000); // margen de 5s
//    }
//
//    @Test
//    void validateToken_WithValidToken_DoesNotThrow() {
//        String token = jwtService.generateToken("testUser", "USER", "uuid-1234");
//        jwtService.validateToken(token); // No debe lanzar excepción
//    }
//
//    @Test
//    void validateToken_WithInvalidToken_ShouldThrowJwtException() {
//        String invalidToken = "this.is.an.invalid.token";
//        assertThatThrownBy(() -> jwtService.validateToken(invalidToken))
//                .isInstanceOf(JwtException.class)
//                .hasMessageContaining("Invalid or tampered token");
//    }
//
//    @Test
//    void validateToken_WithExpiredToken_ShouldThrowExpiredJwtException() {
//        JwtService shortLivedService = new JwtService(jwtSigningKey, 0L); // 0 min duración
//        String token = shortLivedService.generateToken("expiredUser", "USER", "uuid");
//        try {
//            Thread.sleep(1000); // Esperar 1 segundo para garantizar que expire
//        } catch (InterruptedException ignored) {}
//
//        assertThatThrownBy(() -> shortLivedService.validateToken(token))
//                .isInstanceOf(ExpiredJwtException.class)
//                .hasMessageContaining("Token expired but logout successful");
//    }
//
//    @Test
//    void extractBearerToken_WithValidHeader_ReturnsToken() {
//        String token = "abc.def.ghi";
//        String header = "Bearer " + token;
//
//        String result = jwtService.extractBearerToken(header);
//
//        assertThat(result).isEqualTo(token);
//    }
//
//    @Test
//    void extractBearerToken_WithNullHeader_ThrowsJwtException() {
//        assertThatThrownBy(() -> jwtService.extractBearerToken(null))
//                .isInstanceOf(JwtException.class)
//                .hasMessage("Authorization header is missing or malformed");
//    }
//
//    @Test
//    void extractBearerToken_WithMalformedHeader_ThrowsJwtException() {
//        String malformedHeader = "Token abc.def.ghi";
//
//        assertThatThrownBy(() -> jwtService.extractBearerToken(malformedHeader))
//                .isInstanceOf(JwtException.class)
//                .hasMessage("Authorization header is missing or malformed");
//    }
//
//    @Test
//    void extractAllClaims_WithValidToken_ShouldReturnClaims() {
//        String token = jwtService.generateToken("testUser", "USER", "uuid-123");
//        Claims claims = jwtService.extractAllClaims(token);
//
//        assertThat(claims.getSubject()).isEqualTo("testUser");
//        assertThat(claims.get("role", String.class)).isEqualTo("USER");
//        assertThat(claims.get("uuid", String.class)).isEqualTo("uuid-123");
//    }
//
//    @Test
//    void extractAllClaims_WithExpiredToken_ShouldThrowExpiredJwtException() {
//        JwtService shortLivedJwtService = new JwtService(jwtSigningKey, 0L);
//        String token = shortLivedJwtService.generateToken("expiredUser", "USER", "uuid-456");
//
//        try {
//            Thread.sleep(1000);
//        } catch (InterruptedException ignored) {}
//
//        assertThatThrownBy(() -> shortLivedJwtService.extractAllClaims(token))
//                .isInstanceOf(ExpiredJwtException.class)
//                .hasMessageContaining("Token expired");
//    }
//
//    @Test
//    void extractAllClaims_WithInvalidToken_ShouldThrowJwtException() {
//        String invalidToken = "this.is.not.valid";
//
//        assertThatThrownBy(() -> jwtService.extractAllClaims(invalidToken))
//                .isInstanceOf(JwtException.class)
//                .hasMessageContaining("Invalid or tampered token");
//    }
//
//    @Test
//    void switchRole_WithValidChange_ShouldReturnNewToken() {
//        String originalToken = jwtService.generateToken("testUser", "USER", "uuid-001");
//
//        String switchedToken = jwtService.switchRole(originalToken, "ADMIN");
//
//        Claims claims = Jwts.parser()
//                .verifyWith(Keys.hmacShaKeyFor(io.jsonwebtoken.io.Decoders.BASE64.decode(jwtSigningKey)))
//                .build()
//                .parseSignedClaims(switchedToken)
//                .getPayload();
//
//        assertThat(claims.get("role", String.class)).isEqualTo("ADMIN");
//        assertThat(claims.get("isTemporaryRole", Boolean.class)).isTrue();
//        assertThat(claims.get("uuid", String.class)).isEqualTo("uuid-001");
//        assertThat(claims.getSubject()).isEqualTo("testUser");
//    }
//
//    @Test
//    void switchRole_SameRole_ShouldThrowException() {
//        String token = jwtService.generateToken("testUser", "USER", "uuid-002");
//
//        assertThatThrownBy(() -> jwtService.switchRole(token, "USER"))
//                .isInstanceOf(InvalidRoleChangeRequestException.class)
//                .hasMessage("New role is the same as current role.");
//    }
//
//    @Test
//    void switchRole_InvalidRequestedRole_ShouldThrowException() {
//        String token = jwtService.generateToken("testUser", "USER", "uuid-003");
//
//        assertThatThrownBy(() -> jwtService.switchRole(token, "GUEST"))
//                .isInstanceOf(InvalidRoleChangeRequestException.class)
//                .hasMessage("Requested role change is not allowed.");
//    }
//
//    @Test
//    void switchRole_InvalidToken_ShouldThrowJwtException() {
//        String invalidToken = "not.a.valid.token";
//
//        assertThatThrownBy(() -> jwtService.switchRole(invalidToken, "ADMIN"))
//                .isInstanceOf(JwtException.class)
//                .hasMessageContaining("Invalid or tampered token");
//    }
//}


// Node: switchRole_WithValidChange_ShouldReturnNewToken
// Node: isTrue
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


// Node: switchRole_validRoleChange_returnsNewToken
