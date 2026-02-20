// Cluster 1

// Node: validateToken
// Node: extractBearerToken
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

// Node: repos/cloned_ms_repos/ita-challenges-backend/jwt-core/src/main/java/com/itachallenge/jwtcore/service/JwtService.java:JwtService.<init>
// Node: JwtService
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


// Node: extractBearerToken_WithNullHeader_ShouldThrowException
// Node: assertThatThrownBy
// Node: isInstanceOf
// Node: hasMessage
// Node: extractBearerToken_WithMalformedHeader_ShouldThrowException
// Node: extractAllClaims_WithInvalidToken_ShouldThrowJwtException
// Node: hasMessageContaining
// Node: getUserUuIdFromAuthenticationHeader_nullHeader_throwsJwtException
// Node: getUserUuIdFromAuthenticationHeader_malformedHeader_throwsJwtException
// Node: getUserUuIdFromAuthenticationHeader_invalidToken_throwsJwtException
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


// Node: validateToken_WithValidToken_DoesNotThrow
// Node: validateToken_WithInvalidToken_ShouldThrowJwtException
// Node: validateToken_WithExpiredToken_ShouldThrowExpiredJwtException
// Node: sleep
// Node: extractBearerToken_WithValidHeader_ReturnsToken
// Node: extractBearerToken_WithNullHeader_ThrowsJwtException
// Node: extractBearerToken_WithMalformedHeader_ThrowsJwtException
// Node: extractAllClaims_WithExpiredToken_ShouldThrowExpiredJwtException
// Node: switchRole
package com.itachallenge.auth.service;

import io.jsonwebtoken.Claims;

public interface IAuthJwtFacade {

    String generateToken(String username, String role, String uuid);
    void validateToken(String token);
    Claims extractAllClaims(String token);
    String extractBearerToken(String authHeader);

}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-auth/src/main/java/com/itachallenge/auth/service/IAuthJwtFacade.java:IAuthJwtFacade.<init>
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


// Node: switchRole_SameRole_ShouldThrowException
// Node: switchRole_InvalidRequestedRole_ShouldThrowException
// Node: switchRole_InvalidToken_ShouldThrowJwtException
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


// Node: switchRole_invalidRoleChange_throwsException
