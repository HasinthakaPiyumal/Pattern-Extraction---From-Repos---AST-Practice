// Cluster 1

package com.bht.saigonparking.common.interceptor;

import java.util.Map;

import org.apache.logging.log4j.Level;

import com.bht.saigonparking.common.util.LoggingUtil;

import io.grpc.ForwardingServerCall;
import io.grpc.Metadata;
import io.grpc.ServerCall;
import io.grpc.Status;

/**
 *
 * @author bht
 */
public final class SaigonParkingCustomizedServerCall<ReqT, RespT> extends ForwardingServerCall.SimpleForwardingServerCall<ReqT, RespT> {

    private final Map<Class<? extends Throwable>, String> errorCodeMap;

    public SaigonParkingCustomizedServerCall(ServerCall<ReqT, RespT> serverCall,
                                             Map<Class<? extends Throwable>, String> errorCodeMap) {
        super(serverCall);
        this.errorCodeMap = errorCodeMap;
    }

    @Override
    public final void close(Status status, Metadata trailers) {
        if (status.getCode() == Status.Code.UNKNOWN
                && status.getDescription() == null
                && status.getCause() != null && errorCodeMap.containsKey(status.getCause().getClass())) {

            Throwable e = status.getCause();
            LoggingUtil.log(Level.ERROR, "ServerInterceptor", "Exception", e.getClass().getSimpleName());
            status = Status.INTERNAL.withDescription(errorCodeMap.get(e.getClass()));
        }
        super.close(status, trailers);
    }
}

// Node: close
// Node: getCode
// Node: getDescription
// Node: getCause
// Node: withDescription
package com.bht.saigonparking.common.interceptor;

import static com.bht.saigonparking.common.constant.SaigonParkingTransactionalMetadata.AUTHORIZATION_KEY_NAME;
import static com.bht.saigonparking.common.constant.SaigonParkingTransactionalMetadata.INTERNAL_KEY_NAME;

import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Set;

import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;

import org.apache.logging.log4j.Level;

import com.bht.saigonparking.common.auth.SaigonParkingAuthentication;
import com.bht.saigonparking.common.auth.SaigonParkingAuthenticationImpl;
import com.bht.saigonparking.common.auth.SaigonParkingTokenBody;
import com.bht.saigonparking.common.auth.SaigonParkingTokenType;
import com.bht.saigonparking.common.exception.MissingTokenException;
import com.bht.saigonparking.common.exception.PermissionDeniedException;
import com.bht.saigonparking.common.exception.UsernameNotMatchException;
import com.bht.saigonparking.common.exception.WrongTokenTypeException;
import com.bht.saigonparking.common.util.LoggingUtil;
import com.google.common.collect.ImmutableSet;

import io.grpc.Context;
import io.grpc.Contexts;
import io.grpc.Metadata;
import io.grpc.Metadata.Key;
import io.grpc.ServerCall;
import io.grpc.ServerCallHandler;
import io.grpc.ServerInterceptor;
import io.grpc.Status;
import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.MalformedJwtException;
import io.jsonwebtoken.io.DecodingException;
import io.jsonwebtoken.security.SignatureException;
import lombok.Getter;


/**
 *
 * This interceptor is using in gRPC server side
 *
 * This interceptor is using for checking if client's provided token is valid
 * This is using for Authentication and Authorization process in server's side
 *
 * @author bht
 */
public final class SaigonParkingServerInterceptor implements ServerInterceptor {

    private final SaigonParkingAuthentication authentication;
    private final Map<Class<? extends Throwable>, String> errorCodeMap;
    private final Set<String> nonProvideTokenMethodSet;

    @Getter
    private final Context.Key<String> roleContext = Context.key("role");
    @Getter
    private final Context.Key<Long> userIdContext = Context.key("userId");

    private static final Key<String> INTERNAL_SERVICE_KEY = Key.of(INTERNAL_KEY_NAME, Metadata.ASCII_STRING_MARSHALLER);
    private static final Key<String> AUTHORIZATION_KEY = Key.of(AUTHORIZATION_KEY_NAME, Metadata.ASCII_STRING_MARSHALLER);

    public SaigonParkingServerInterceptor() {
        this(Collections.emptyMap());
    }


    public SaigonParkingServerInterceptor(Map<Class<? extends Throwable>, String> errorCodeMap) {
        authentication = new SaigonParkingAuthenticationImpl();
        this.errorCodeMap = errorCodeMap;

        /* not check token forgrpc  health checking api */
        nonProvideTokenMethodSet = new ImmutableSet.Builder<String>()
                .add("grpc.health.v1.Health/Check")
                .add("grpc.health.v1.Health/Watch")
                .build();
    }


    @Override
    public <ReqT, RespT> ServerCall.Listener<ReqT> interceptCall(ServerCall<ReqT, RespT> serverCall,
                                                                 Metadata metadata,
                                                                 ServerCallHandler<ReqT, RespT> serverCallHandler) {

        /* init new call listener */
        ServerCall.Listener<ReqT> newCallListener = new ServerCall.Listener<ReqT>() {
        };

        long userId;
        String userRole;

        /* get metadata from header of incoming request */
        String token = metadata.get(AUTHORIZATION_KEY);
        String internalServiceCodeString = metadata.get(INTERNAL_SERVICE_KEY);

        /* Method's full name, eg. com.bht.saigonparking.api.grpc.auth.AuthService/registerUser */
        String fullMethodName = serverCall.getMethodDescriptor().getFullMethodName();
        LoggingUtil.log(Level.INFO, "ServerInterceptor", "FullMethodName", fullMethodName);

        try {
            if (nonProvideTokenMethodSet.contains(fullMethodName)) { /* method skip check token => HealthService */

                userId = 0L;
                userRole = "UNRECOGNIZED";

            } else if (token == null && internalServiceCodeString == null) { /* spam requests */
                throw new MissingTokenException();

            } else if (token != null) { /* external requests */

                SaigonParkingTokenBody tokenBody = authentication.parseJwtToken(token);

                if (!tokenBody.getTokenType().equals(SaigonParkingTokenType.ACCESS_TOKEN)) {
                    throw new WrongTokenTypeException();
                }

                userId = tokenBody.getUserId();
                userRole = tokenBody.getUserRole();

            } else { /* internal requests */

                userRole = "ADMIN";
                userId = 1L;
            }

        } catch (ExpiredJwtException expiredJwtException) {
            serverCall.close(Status.UNAUTHENTICATED.withDescription("SPE#00001"), metadata);
            LoggingUtil.log(Level.ERROR, "ServerInterceptor", "Exception", "ExpiredJwtException");
            return newCallListener;

        } catch (SignatureException signatureException) {
            serverCall.close(Status.UNAUTHENTICATED.withDescription("SPE#00002"), metadata);
            LoggingUtil.log(Level.ERROR, "ServerInterceptor", "Exception", "SignatureException");
            return newCallListener;

        } catch (MalformedJwtException malformedJwtException) {
            serverCall.close(Status.UNAUTHENTICATED.withDescription("SPE#00003"), metadata);
            LoggingUtil.log(Level.ERROR, "ServerInterceptor", "Exception", "MalformedJwtException");
            return newCallListener;

        } catch (DecodingException decodingException) {
            serverCall.close(Status.UNAUTHENTICATED.withDescription("SPE#00004"), metadata);
            LoggingUtil.log(Level.ERROR, "ServerInterceptor", "Exception", "DecodingException");
            return newCallListener;

        } catch (MissingTokenException missingTokenException) {
            serverCall.close(Status.UNAUTHENTICATED.withDescription("SPE#00005"), metadata);
            LoggingUtil.log(Level.ERROR, "ServerInterceptor", "Exception", "MissingTokenException");
            return newCallListener;

        } catch (WrongTokenTypeException wrongTokenException) {
            serverCall.close(Status.UNAUTHENTICATED.withDescription("SPE#00006"), metadata);
            LoggingUtil.log(Level.ERROR, "ServerInterceptor", "Exception", "WrongTokenTypeException");
            return newCallListener;

        } catch (Exception exception) {
            serverCall.close(Status.INTERNAL.withDescription("SPE#00000"), metadata);
            LoggingUtil.log(Level.ERROR, "ServerInterceptor", "Exception", exception.getClass().getSimpleName());
            return newCallListener;
        }

        ServerCall<ReqT, RespT> wrappedServerCall = new SaigonParkingCustomizedServerCall<>(serverCall, errorCodeMap);

        return Contexts.interceptCall(Context.current()
                        .withValue(roleContext, userRole)
                        .withValue(userIdContext, userId),
                wrappedServerCall,
                metadata,
                serverCallHandler);
    }


    public void validateAdmin() {
        validateUserRole("ADMIN");
    }


    public void validateUser(@NotNull Long userEntityId) {
        if (!userIdContext.get().equals(userEntityId)) {
            throw new UsernameNotMatchException();
        }
    }


    public void validateUserRole(@NotEmpty String acceptedRole) {
        if (!acceptedRole.equals(roleContext.get())) {
            throw new PermissionDeniedException();
        }
    }


    public void validateUserRole(@NotEmpty List<String> acceptedRoles) {
        if (!acceptedRoles.contains(roleContext.get())) {
            throw new PermissionDeniedException();
        }
    }
}

// Node: parseJwtToken
// Node: getTokenType
// Node: WrongTokenTypeException
// Node: getUserId
// Node: getUserRole
// Node: current
// Node: withValue
package com.bht.saigonparking.common.auth;

import java.util.UUID;

import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;

import org.springframework.data.util.Pair;

/**
 *
 * authentication with JWT token, support by JJWT library
 * using for Saigon Parking project only
 *
 * @author bht
 */
public interface SaigonParkingAuthentication {

    SaigonParkingTokenBody parseJwtToken(@NotEmpty String jsonWebToken);

    /* 1st: tokenId, 2nd: token */
    Pair<UUID, String> generateAccessToken(@NotNull Long userId, @NotEmpty String userRole);

    /* 1st: tokenId, 2nd: token */
    Pair<UUID, String> generateRefreshToken(@NotNull Long userId, @NotEmpty String userRole);

    /* 1st: tokenId, 2nd: token */
    Pair<UUID, String> generateActivateAccountToken(@NotNull Long userId, @NotEmpty String userRole);

    /* 1st: tokenId, 2nd: token */
    Pair<UUID, String> generateResetPasswordToken(@NotNull Long userId, @NotEmpty String userRole);
}

// Node: repos/cloned_ms_repos/saigonparking/common/src/main/java/com/bht/saigonparking/common/auth/SaigonParkingAuthentication.java:SaigonParkingAuthentication.<init>
// Node: generateAccessToken
// Node: generateRefreshToken
// Node: generateActivateAccountToken
// Node: generateResetPasswordToken
// Node: generateJwtToken
package com.bht.saigonparking.common.auth;

import static com.bht.saigonparking.common.auth.SaigonParkingTokenType.*;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.Key;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Base64;
import java.util.Date;
import java.util.Objects;
import java.util.Properties;
import java.util.Random;
import java.util.UUID;

import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;

import org.apache.logging.log4j.Level;
import org.springframework.data.util.Pair;

import com.bht.saigonparking.common.util.LoggingUtil;
import com.fasterxml.uuid.Generators;
import com.fasterxml.uuid.impl.TimeBasedGenerator;
import com.google.common.io.ByteStreams;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;

/**
 *
 * @author bht
 */
public final class SaigonParkingAuthenticationImpl implements SaigonParkingAuthentication {

    private static final String SAIGON_PARKING_ISSUER = "www.saigonparking.wtf";
    private static final short MAX_RANDOM_EXCLUSIVE = 1000;
    private static final TimeBasedGenerator UUID_GENERATOR = Generators.timeBasedGenerator();

    private static final String USER_ROLE_KEY_NAME = "role";
    private static final String FACTOR_KEY_NAME = "fac";
    private static final String TOKEN_TYPE_KEY_NAME = "classification";

    private Long userIdDecodeKey;
    private Key secretKey;

    public SaigonParkingAuthenticationImpl() {
        Properties properties = new Properties();
        try {
            properties.load(Objects.requireNonNull(SaigonParkingAuthenticationImpl.class
                    .getClassLoader()
                    .getResourceAsStream("common.properties")));

            userIdDecodeKey = Long.valueOf((String) properties.get("token.user-id.decode.key"));
            secretKey = getSecretKey((String) properties.get("token.rsa-private-key.path"));

        } catch (IOException e) {
            LoggingUtil.log(Level.ERROR, "AUTH", "Read resource", "Resource is unavailable !");
        }
    }

    private Long encryptUserId(@NotNull Long userId, @NotNull Integer factor) {
        return userId ^ (userIdDecodeKey * factor);
    }

    private Long decryptUserId(@NotNull Long encodedUserId, @NotNull Integer factor) {
        return encodedUserId ^ (userIdDecodeKey * factor);
    }

    private Key getSecretKey(@NotEmpty String keyPath) throws IOException {
        return Keys.hmacShaKeyFor(getSecretKeyByteArray(keyPath));
    }

    private byte[] getSecretKeyByteArray(@NotEmpty String keyPath) throws IOException {
        return Base64.getDecoder()
                .decode(new String(ByteStreams.toByteArray(Objects
                        .requireNonNull(SaigonParkingAuthenticationImpl.class
                                .getClassLoader()
                                .getResourceAsStream(keyPath))))
                        .replace("-----BEGIN RSA PRIVATE KEY-----", "")
                        .replace("-----END RSA PRIVATE KEY-----", "")
                        .replaceAll("\\n", "")
                        .getBytes(StandardCharsets.UTF_8));
    }

    private Pair<UUID, String> generateJwtToken(@NotNull SaigonParkingTokenType type,
                                                @NotNull Long userId,
                                                @NotEmpty String userRole,
                                                @NotNull Integer timeAmount,
                                                @NotNull ChronoUnit timeUnit) {
        Instant now = Instant.now();
        Integer factor = new Random().nextInt(MAX_RANDOM_EXCLUSIVE);
        UUID tokenUuid = UUID_GENERATOR.generate();

        return Pair.of(tokenUuid, Jwts.builder()
                .setId(tokenUuid.toString())
                .setIssuer(SAIGON_PARKING_ISSUER)
                .claim(USER_ROLE_KEY_NAME, userRole)
                .claim(FACTOR_KEY_NAME, factor)
                .claim(TOKEN_TYPE_KEY_NAME, type)
                .setSubject(encryptUserId(userId, factor).toString())
                .setIssuedAt(Date.from(now))
                .setExpiration(Date.from(now.plus(timeAmount, timeUnit)))
                .signWith(secretKey)
                .compact());
    }

    @Override
    public SaigonParkingTokenBody parseJwtToken(@NotEmpty String jsonWebToken) {
        String realToken = jsonWebToken.replace("Bearer", "").replace(" ", "");
        Claims tokenBody = Jwts.parserBuilder().setSigningKey(secretKey).build()
                .parseClaimsJws(realToken)
                .getBody();

        return SaigonParkingTokenBody.builder()
                .tokenId(tokenBody.getId())
                .tokenType(SaigonParkingTokenType.valueOf(tokenBody.get(TOKEN_TYPE_KEY_NAME, String.class)))
                .userId(decryptUserId(Long.valueOf(tokenBody.getSubject()), tokenBody.get(FACTOR_KEY_NAME, Integer.class)))
                .userRole(tokenBody.get(USER_ROLE_KEY_NAME, String.class))
                .exp(tokenBody.getExpiration())
                .build();
    }

    @Override
    public Pair<UUID, String> generateAccessToken(@NotNull Long userId, @NotEmpty String userRole) {
        return generateJwtToken(ACCESS_TOKEN, userId, userRole, 30, ChronoUnit.MINUTES);
    }

    @Override
    public Pair<UUID, String> generateRefreshToken(@NotNull Long userId, @NotEmpty String userRole) {
        return generateJwtToken(REFRESH_TOKEN, userId, userRole, 30, ChronoUnit.DAYS);
    }

    @Override
    public Pair<UUID, String> generateActivateAccountToken(@NotNull Long userId, @NotEmpty String userRole) {
        return generateJwtToken(ACTIVATE_TOKEN, userId, userRole, 5, ChronoUnit.MINUTES);
    }

    @Override
    public Pair<UUID, String> generateResetPasswordToken(@NotNull Long userId, @NotEmpty String userRole) {
        return generateJwtToken(RESET_PW_TOKEN, userId, userRole, 5, ChronoUnit.MINUTES);
    }
}

// Node: Date
package com.bht.saigonparking.service.auth.interceptor;

import static com.bht.saigonparking.common.constant.SaigonParkingTransactionalMetadata.AUTHORIZATION_KEY_NAME;
import static com.bht.saigonparking.common.constant.SaigonParkingTransactionalMetadata.INTERNAL_KEY_NAME;

import java.util.Date;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

import javax.persistence.EntityNotFoundException;

import org.apache.logging.log4j.Level;
import org.lognet.springboot.grpc.GRpcGlobalInterceptor;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.dao.EmptyResultDataAccessException;
import org.springframework.orm.ObjectOptimisticLockingFailureException;

import com.bht.saigonparking.common.auth.SaigonParkingAuthentication;
import com.bht.saigonparking.common.auth.SaigonParkingAuthenticationImpl;
import com.bht.saigonparking.common.auth.SaigonParkingTokenBody;
import com.bht.saigonparking.common.auth.SaigonParkingTokenType;
import com.bht.saigonparking.common.exception.InvalidRefreshTokenException;
import com.bht.saigonparking.common.exception.MissingTokenException;
import com.bht.saigonparking.common.exception.PermissionDeniedException;
import com.bht.saigonparking.common.exception.UserAlreadyActivatedException;
import com.bht.saigonparking.common.exception.UserNotActivatedException;
import com.bht.saigonparking.common.exception.UsernameNotMatchException;
import com.bht.saigonparking.common.exception.WrongPasswordException;
import com.bht.saigonparking.common.exception.WrongTokenTypeException;
import com.bht.saigonparking.common.exception.WrongUserRoleException;
import com.bht.saigonparking.common.interceptor.SaigonParkingCustomizedServerCall;
import com.bht.saigonparking.common.util.LoggingUtil;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;

import io.grpc.Context;
import io.grpc.Contexts;
import io.grpc.Metadata;
import io.grpc.Metadata.Key;
import io.grpc.ServerCall;
import io.grpc.ServerCallHandler;
import io.grpc.ServerInterceptor;
import io.grpc.Status;
import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.MalformedJwtException;
import io.jsonwebtoken.io.DecodingException;
import io.jsonwebtoken.security.SignatureException;
import lombok.Getter;
import lombok.extern.log4j.Log4j2;


/**
 *
 * This interceptor is using in gRPC server side
 * Customized Saigon Parking Server Interceptor for Auth Service only !!!!!!!
 *
 * This interceptor is using for checking if client's provided token is valid
 * This is using for Authentication and Authorization process in server's side
 *
 * @author bht
 */
@Log4j2
@GRpcGlobalInterceptor
public final class AuthServiceInterceptor implements ServerInterceptor {

    private final SaigonParkingAuthentication authentication;
    private final Set<String> nonProvideTokenMethodSet;
    private final Map<Class<? extends Throwable>, String> errorCodeMap;

    @Getter
    private final Context.Key<Long> userIdContext = Context.key("userId");
    @Getter
    private final Context.Key<String> userRoleContext = Context.key("userRole");
    @Getter
    private final Context.Key<UUID> tokenIdContext = Context.key("tokenId");
    @Getter
    private final Context.Key<SaigonParkingTokenType> tokenTypeContext = Context.key("tokenType");
    @Getter
    private final Context.Key<Date> expContext = Context.key("exp");

    private static final Key<String> INTERNAL_SERVICE_KEY = Key.of(INTERNAL_KEY_NAME, Metadata.ASCII_STRING_MARSHALLER);
    private static final Key<String> AUTHORIZATION_KEY = Key.of(AUTHORIZATION_KEY_NAME, Metadata.ASCII_STRING_MARSHALLER);

    public AuthServiceInterceptor() {

        authentication = new SaigonParkingAuthenticationImpl();

        nonProvideTokenMethodSet = new ImmutableSet.Builder<String>()
                .add("com.bht.saigonparking.api.grpc.auth.AuthService/validateUser")
                .add("com.bht.saigonparking.api.grpc.auth.AuthService/registerUser")
                .add("com.bht.saigonparking.api.grpc.auth.AuthService/sendResetPasswordEmail")
                .add("com.bht.saigonparking.api.grpc.auth.AuthService/sendActivateAccountEmail")
                .add("com.bht.saigonparking.api.grpc.auth.AuthService/checkEmailAlreadyExist")
                .add("com.bht.saigonparking.api.grpc.auth.AuthService/checkUsernameAlreadyExist")
                .build();

        errorCodeMap = new ImmutableMap.Builder<Class<? extends Throwable>, String>()
                .put(WrongTokenTypeException.class, "SPE#00006")
                .put(InvalidRefreshTokenException.class, "SPE#00007")
                .put(EntityNotFoundException.class, "SPE#00008")
                .put(DataIntegrityViolationException.class, "SPE#00009")
                .put(UserAlreadyActivatedException.class, "SPE#00010")
                .put(UserNotActivatedException.class, "SPE#00011")
                .put(WrongUserRoleException.class, "SPE#00012")
                .put(WrongPasswordException.class, "SPE#00013")
                .put(UsernameNotMatchException.class, "SPE#00014")
                .put(PermissionDeniedException.class, "SPE#00015")
                .put(ObjectOptimisticLockingFailureException.class, "SPE#00016")
                .put(EmptyResultDataAccessException.class, "SPE#00018")
                .build();
    }

    @Override
    public <ReqT, RespT> ServerCall.Listener<ReqT> interceptCall(ServerCall<ReqT, RespT> serverCall,
                                                                 Metadata metadata,
                                                                 ServerCallHandler<ReqT, RespT> serverCallHandler) {

        ServerCall.Listener<ReqT> newCallListener = new ServerCall.Listener<ReqT>() {
        };

        long userId;
        String userRole;
        String tokenId;
        SaigonParkingTokenType tokenType;
        Date exp;

        /* get metadata from header of incoming request */
        String token = metadata.get(AUTHORIZATION_KEY);
        String internalServiceCodeString = metadata.get(INTERNAL_SERVICE_KEY);

        /* Method's full name, eg. com.bht.saigonparking.api.grpc.auth.AuthService/registerUser */
        String fullMethodName = serverCall.getMethodDescriptor().getFullMethodName();
        LoggingUtil.log(Level.INFO, "ServerInterceptor", "FullMethodName", fullMethodName);

        try {
            if (nonProvideTokenMethodSet.contains(fullMethodName)) { /* method skip check token => AuthService */

                userId = 0L;
                userRole = "UNRECOGNIZED";
                tokenId = null;
                tokenType = null;
                exp = new Date();

            } else if (token == null && internalServiceCodeString == null) { /* spam requests */
                throw new MissingTokenException();

            } else if (token != null) { /* external requests */

                SaigonParkingTokenBody tokenBody = authentication.parseJwtToken(token);

                userId = tokenBody.getUserId();
                userRole = tokenBody.getUserRole();
                tokenId = tokenBody.getTokenId();
                tokenType = tokenBody.getTokenType();
                exp = tokenBody.getExp();

            } else { /* internal requests */

                userId = 1L;
                userRole = "ADMIN";
                tokenId = null;
                tokenType = null;
                exp = new Date();
            }

        } catch (ExpiredJwtException expiredJwtException) {
            serverCall.close(Status.UNAUTHENTICATED.withDescription("SPE#00001"), metadata);
            LoggingUtil.log(Level.ERROR, "ServerInterceptor", "Exception", "ExpiredJwtException");
            return newCallListener;

        } catch (SignatureException signatureException) {
            serverCall.close(Status.UNAUTHENTICATED.withDescription("SPE#00002"), metadata);
            LoggingUtil.log(Level.ERROR, "ServerInterceptor", "Exception", "SignatureException");
            return newCallListener;

        } catch (MalformedJwtException malformedJwtException) {
            serverCall.close(Status.UNAUTHENTICATED.withDescription("SPE#00003"), metadata);
            LoggingUtil.log(Level.ERROR, "ServerInterceptor", "Exception", "MalformedJwtException");
            return newCallListener;

        } catch (DecodingException decodingException) {
            serverCall.close(Status.UNAUTHENTICATED.withDescription("SPE#00004"), metadata);
            LoggingUtil.log(Level.ERROR, "ServerInterceptor", "Exception", "DecodingException");
            return newCallListener;

        } catch (MissingTokenException missingTokenException) {
            serverCall.close(Status.UNAUTHENTICATED.withDescription("SPE#00005"), metadata);
            LoggingUtil.log(Level.ERROR, "ServerInterceptor", "Exception", "MissingTokenException");
            return newCallListener;

        } catch (Exception exception) {
            serverCall.close(Status.INTERNAL.withDescription("SPE#00000"), metadata);
            LoggingUtil.log(Level.ERROR, "ServerInterceptor", "Exception", exception.getClass().getSimpleName());
            return newCallListener;
        }

        ServerCall<ReqT, RespT> wrappedServerCall = new SaigonParkingCustomizedServerCall<>(serverCall, errorCodeMap);

        return Contexts.interceptCall(Context.current()
                        .withValue(userIdContext, userId)
                        .withValue(userRoleContext, userRole)
                        .withValue(tokenIdContext, (tokenId != null) ? UUID.fromString(tokenId) : null)
                        .withValue(tokenTypeContext, tokenType)
                        .withValue(expContext, exp),
                wrappedServerCall,
                metadata,
                serverCallHandler);
    }
}

// Node: getTokenId
// Node: getExp
package com.bht.saigonparking.service.auth.service;

import java.util.Date;
import java.util.UUID;

import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;

import org.apache.commons.lang3.tuple.Triple;
import org.springframework.data.util.Pair;

import com.bht.saigonparking.api.grpc.auth.RegisterRequest;
import com.bht.saigonparking.api.grpc.user.UserRole;

/**
 *
 * @author bht
 */
public interface AuthService {

    /**
     *
     * @return triple of:
     * 1st: accessToken
     * 2nd: refreshToken
     */
    Pair<String, String> validateLogin(@NotEmpty String username,
                                       @NotEmpty String password,
                                       @NotNull UserRole userRole);

    /**
     *
     * @return user's email if succeed
     */
    String registerUser(@NotNull RegisterRequest request);

    /**
     *
     * @return user's email if succeed
     */
    String sendResetPasswordEmail(@NotEmpty String username);

    /**
     *
     * @return user's email if succeed
     */
    String sendActivateAccountEmail(@NotEmpty String username);

    /**
     *
     * @return triple of:
     * left:   username
     * middle: accessToken
     * right:  refreshToken
     */
    Triple<String, String, String> generateNewToken(@NotNull Long userId,
                                                    @NotNull Date currentExp,
                                                    @NotEmpty UUID currentTokenId,
                                                    boolean currentIsRefreshToken);

    /**
     *
     * @return triple of:
     * left:   username
     * middle: accessToken
     * right:  refreshToken
     */
    Triple<String, String, String> activateNewAccount(@NotNull Long userId,
                                                      @NotNull Date currentExp,
                                                      @NotEmpty UUID currentTokenId,
                                                      boolean currentIsRefreshToken);
}

// Node: repos/cloned_ms_repos/saigonparking/service/auth-service/src/main/java/com/bht/saigonparking/service/auth/service/AuthService.java:AuthService.<init>
// Node: validateLogin
// Node: registerUser
// Node: sendResetPasswordEmail
// Node: sendActivateAccountEmail
// Node: generateNewToken
// Node: activateNewAccount
// Node: getPassword
// Node: getRole
// Node: setAccessToken
// Node: getFirst
// Node: setRefreshToken
// Node: getSecond
package com.bht.saigonparking.service.auth.service.grpc;

import org.apache.commons.lang3.tuple.Triple;
import org.apache.logging.log4j.Level;
import org.lognet.springboot.grpc.GRpcService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.util.Pair;

import com.bht.saigonparking.api.grpc.auth.AuthServiceGrpc;
import com.bht.saigonparking.api.grpc.auth.RefreshTokenResponse;
import com.bht.saigonparking.api.grpc.auth.RegisterRequest;
import com.bht.saigonparking.api.grpc.auth.ValidateRequest;
import com.bht.saigonparking.api.grpc.auth.ValidateResponse;
import com.bht.saigonparking.api.grpc.user.UserServiceGrpc;
import com.bht.saigonparking.common.auth.SaigonParkingTokenType;
import com.bht.saigonparking.common.exception.WrongTokenTypeException;
import com.bht.saigonparking.common.util.LoggingUtil;
import com.bht.saigonparking.service.auth.interceptor.AuthServiceInterceptor;
import com.bht.saigonparking.service.auth.service.AuthService;
import com.google.protobuf.BoolValue;
import com.google.protobuf.Empty;
import com.google.protobuf.StringValue;

import io.grpc.stub.StreamObserver;
import lombok.AllArgsConstructor;

/**
 *
 * @author bht
 */
@GRpcService
@AllArgsConstructor(onConstructor = @__(@Autowired))
public final class AuthServiceGrpcImpl extends AuthServiceGrpc.AuthServiceImplBase {

    private final AuthService authService;
    private final AuthServiceInterceptor authServiceInterceptor;

    private final UserServiceGrpc.UserServiceBlockingStub userServiceBlockingStub;

    @Override
    public void checkUsernameAlreadyExist(StringValue request, StreamObserver<BoolValue> responseObserver) {
        try {
            BoolValue isUsernameAlreadyExist = userServiceBlockingStub.checkUsernameAlreadyExist(request);

            responseObserver.onNext(isUsernameAlreadyExist);
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("checkUsernameAlreadyExist(%s): %b", request.getValue(), isUsernameAlreadyExist.getValue()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("checkUsernameAlreadyExist(%s)", request.getValue()));
        }
    }

    @Override
    public void checkEmailAlreadyExist(StringValue request, StreamObserver<BoolValue> responseObserver) {
        try {
            BoolValue isEmailAlreadyExist = userServiceBlockingStub.checkEmailAlreadyExist(request);

            responseObserver.onNext(isEmailAlreadyExist);
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("checkEmailAlreadyExist(%s): %b", request.getValue(), isEmailAlreadyExist.getValue()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("checkEmailAlreadyExist(%s)", request.getValue()));
        }
    }

    @Override
    public void validateUser(ValidateRequest request, StreamObserver<ValidateResponse> responseObserver) {
        try {
            Pair<String, String> validateResponseTriple = authService.validateLogin(
                    request.getUsername(),
                    request.getPassword(),
                    request.getRole());

            ValidateResponse validateResponse = ValidateResponse.newBuilder()
                    .setAccessToken(validateResponseTriple.getFirst())
                    .setRefreshToken(validateResponseTriple.getSecond())
                    .build();

            responseObserver.onNext(validateResponse);
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("validateUser(%s, %s)", request.getUsername(), request.getRole()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("validateUser(%s, %s, %s)",
                            request.getUsername(), request.getPassword(), request.getRole()));
        }
    }

    @Override
    public void registerUser(RegisterRequest request, StreamObserver<StringValue> responseObserver) {
        try {
            StringValue email = StringValue.of(authService.registerUser(request));

            responseObserver.onNext(email);
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("registerUser(%s)", request.getUsername()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("registerUser(%s)", request.getUsername()));
        }
    }

    @Override
    public void sendResetPasswordEmail(StringValue request, StreamObserver<StringValue> responseObserver) {
        try {
            StringValue email = StringValue.of(authService.sendResetPasswordEmail(request.getValue()));

            responseObserver.onNext(email);
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("sendResetPasswordEmail(%s)", request.getValue()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("sendResetPasswordEmail(%s)", request.getValue()));
        }
    }

    @Override
    public void sendActivateAccountEmail(StringValue request, StreamObserver<StringValue> responseObserver) {
        try {
            StringValue email = StringValue.of(authService.sendActivateAccountEmail(request.getValue()));

            responseObserver.onNext(email);
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("sendActivateAccountEmail(%s)", request.getValue()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("sendActivateAccountEmail(%s)", request.getValue()));
        }
    }

    @Override
    public void generateNewToken(Empty request, StreamObserver<RefreshTokenResponse> responseObserver) {
        Long userId = authServiceInterceptor.getUserIdContext().get();
        try {
            SaigonParkingTokenType tokenType = authServiceInterceptor.getTokenTypeContext().get();

            if (tokenType.equals(SaigonParkingTokenType.ACCESS_TOKEN)) {
                throw new WrongTokenTypeException();
            }

            Triple<String, String, String> refreshTokenTriple = authService.generateNewToken(
                    userId,
                    authServiceInterceptor.getExpContext().get(),
                    authServiceInterceptor.getTokenIdContext().get(),
                    tokenType.equals(SaigonParkingTokenType.REFRESH_TOKEN));

            RefreshTokenResponse refreshTokenResponse = RefreshTokenResponse.newBuilder()
                    .setUsername(refreshTokenTriple.getLeft())
                    .setAccessToken(refreshTokenTriple.getMiddle())
                    .setRefreshToken(refreshTokenTriple.getRight())
                    .build();

            responseObserver.onNext(refreshTokenResponse);
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("generateNewToken(%d)", userId));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("generateNewToken(%d)", userId));
        }
    }

    @Override
    public void activateNewAccount(Empty request, StreamObserver<RefreshTokenResponse> responseObserver) {
        Long userId = authServiceInterceptor.getUserIdContext().get();
        try {
            SaigonParkingTokenType tokenType = authServiceInterceptor.getTokenTypeContext().get();

            if (!tokenType.equals(SaigonParkingTokenType.ACTIVATE_TOKEN)) {
                throw new WrongTokenTypeException();
            }

            Triple<String, String, String> refreshTokenTriple = authService.activateNewAccount(
                    userId,
                    authServiceInterceptor.getExpContext().get(),
                    authServiceInterceptor.getTokenIdContext().get(),
                    false);

            RefreshTokenResponse refreshTokenResponse = RefreshTokenResponse.newBuilder()
                    .setUsername(refreshTokenTriple.getLeft())
                    .setAccessToken(refreshTokenTriple.getMiddle())
                    .setRefreshToken(refreshTokenTriple.getRight())
                    .build();

            responseObserver.onNext(refreshTokenResponse);
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("activateNewAccount(%d)", userId));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("activateNewAccount(%d)", userId));
        }
    }
}

// Node: getTokenTypeContext
// Node: getExpContext
// Node: getTokenIdContext
// Node: setUsername
// Node: getLeft
// Node: getMiddle
// Node: getRight
// Node: sendMail
// Node: setEmail
package com.bht.saigonparking.service.auth.service.impl;

import static com.bht.saigonparking.api.grpc.mail.MailRequestType.ACTIVATE_ACCOUNT;
import static com.bht.saigonparking.api.grpc.mail.MailRequestType.RESET_PASSWORD;

import java.util.Date;
import java.util.UUID;

import javax.persistence.EntityNotFoundException;
import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;

import org.apache.commons.lang3.tuple.Triple;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.util.Pair;
import org.springframework.security.crypto.bcrypt.BCrypt;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.bht.saigonparking.api.grpc.auth.RegisterRequest;
import com.bht.saigonparking.api.grpc.user.Customer;
import com.bht.saigonparking.api.grpc.user.User;
import com.bht.saigonparking.api.grpc.user.UserRole;
import com.bht.saigonparking.api.grpc.user.UserServiceGrpc;
import com.bht.saigonparking.common.auth.SaigonParkingAuthentication;
import com.bht.saigonparking.common.exception.InvalidRefreshTokenException;
import com.bht.saigonparking.common.exception.UserAlreadyActivatedException;
import com.bht.saigonparking.common.exception.UserNotActivatedException;
import com.bht.saigonparking.common.exception.WrongPasswordException;
import com.bht.saigonparking.common.exception.WrongUserRoleException;
import com.bht.saigonparking.service.auth.repository.UserTokenRepository;
import com.bht.saigonparking.service.auth.service.AuthService;
import com.google.protobuf.Int64Value;
import com.google.protobuf.StringValue;

import io.grpc.Context;
import lombok.AllArgsConstructor;

/**
 *
 * @author bht
 */
@Service
@Transactional
@AllArgsConstructor(onConstructor = @__(@Autowired))
public class AuthServiceImpl implements AuthService {

    private final UserTokenRepository userTokenRepository;
    private final SaigonParkingAuthentication authentication;
    private final AuthServiceHelperImpl authServiceImplHelper;
    private final UserServiceGrpc.UserServiceBlockingStub userServiceBlockingStub;

    @Override
    public Pair<String, String> validateLogin(@NotEmpty String username,
                                              @NotEmpty String password,
                                              @NotNull UserRole userRole) {

        User user = userServiceBlockingStub.getUserByUsername(StringValue.of(username));

        if (user.getRole().equals(userRole)) {
            if (Boolean.TRUE.equals(user.getIsActivated())) {
                if (BCrypt.checkpw(password, user.getPassword())) {

                    /* Asynchronously update user last sign in */
                    Context context = Context.current().fork();
                    context.run(() -> authServiceImplHelper.updateUserLastSignIn(user.getId()));

                    /* Generate new access token, new refresh token for user with Id, Role */
                    Pair<UUID, String> generatedAccessToken = authentication.generateAccessToken(user.getId(), user.getRole().toString());
                    Pair<UUID, String> generatedRefreshToken = authentication.generateRefreshToken(user.getId(), user.getRole().toString());

                    /* Asynchronously save user token to the database */
                    authServiceImplHelper.saveUserRefreshToken(user.getId(), generatedRefreshToken.getFirst());

                    /* Return response with two field: 1st ResponseType, 2nd AccessToken */
                    return Pair.of(generatedAccessToken.getSecond(), generatedRefreshToken.getSecond());
                }
                throw new WrongPasswordException();
            }
            throw new UserNotActivatedException();
        }
        throw new WrongUserRoleException();
    }

    @Override
    public String registerUser(@NotNull RegisterRequest request) {
        UserRole userRole = UserRole.CUSTOMER;
        Long userId = userServiceBlockingStub.createCustomer(Customer.newBuilder()
                .setUserInfo(User.newBuilder()
                        .setUsername(request.getUsername())
                        .setPassword(request.getPassword())
                        .setEmail(request.getEmail())
                        .setRole(userRole)
                        .build())
                .setFirstName(request.getFirstName())
                .setLastName(request.getLastName())
                .setPhone(request.getPhone())
                .build())
                .getValue();

        String activateAccountToken = authentication.generateActivateAccountToken(userId, userRole.toString()).getSecond();
        authServiceImplHelper.sendMail(ACTIVATE_ACCOUNT, request.getEmail(), request.getUsername(), activateAccountToken);

        return request.getEmail();
    }

    @Override
    public String sendResetPasswordEmail(@NotEmpty String username) {
        User user = userServiceBlockingStub.getUserByUsername(StringValue.of(username));

        /* Only send reset password email if user is already activated !!! */
        if (!user.getIsActivated()) {
            throw new UserNotActivatedException();
        }

        String resetPasswordToken = authentication.generateResetPasswordToken(user.getId(), user.getRole().toString()).getSecond();

        authServiceImplHelper.sendMail(RESET_PASSWORD, user.getEmail(), username, resetPasswordToken);
        return user.getEmail();
    }

    @Override
    public String sendActivateAccountEmail(@NotEmpty String username) {
        User user = userServiceBlockingStub.getUserByUsername(StringValue.of(username));

        /* Only send activate email if user is not activated yet !!! */
        if (user.getIsActivated()) {
            throw new UserAlreadyActivatedException();
        }

        String activateAccountToken = authentication.generateActivateAccountToken(user.getId(), user.getRole().toString()).getSecond();

        authServiceImplHelper.sendMail(ACTIVATE_ACCOUNT, user.getEmail(), username, activateAccountToken);
        return user.getEmail();
    }

    @Override
    public Triple<String, String, String> generateNewToken(@NotNull Long userId,
                                                           @NotNull Date currentExp,
                                                           @NotEmpty UUID currentTokenId,
                                                           boolean currentIsRefreshToken) {

        User user = userServiceBlockingStub.getUserById(Int64Value.of(userId));

        return generateNewToken(user, currentExp, currentTokenId, currentIsRefreshToken);
    }

    @Override
    public Triple<String, String, String> activateNewAccount(@NotNull Long userId,
                                                             @NotNull Date currentExp,
                                                             @NotEmpty UUID currentTokenId,
                                                             boolean currentIsRefreshToken) {

        User user = userServiceBlockingStub.getUserById(Int64Value.of(userId));

        /* Asynchronously activate user */
        Context context = Context.current().fork();
        context.run(() -> authServiceImplHelper.activateUserWithId(userId));

        return generateNewToken(user, currentExp, currentTokenId, currentIsRefreshToken);
    }

    @SuppressWarnings("java:S2201")
    private Triple<String, String, String> generateNewToken(@NotNull User user,
                                                            @NotNull Date currentExp,
                                                            @NotEmpty UUID currentTokenId,
                                                            boolean currentIsRefreshToken) {
        try {
            if (currentIsRefreshToken) {
                userTokenRepository.findByTokenId(currentTokenId).orElseThrow(EntityNotFoundException::new);
                userTokenRepository.flush();
            }
        } catch (EntityNotFoundException entityNotFoundException) {
            throw new InvalidRefreshTokenException();
        }

        Pair<UUID, String> generatedAccessToken = authentication.generateAccessToken(user.getId(), user.getRole().toString());

        if (((currentExp.getTime() - new Date().getTime()) / 86400000) > 7) { /* Token not nearly expire */
            return Triple.of(user.getUsername(), generatedAccessToken.getSecond(), "");

        } else { /* Token nearly expire */

            /* Generate new refresh token for user with Id, Role */
            Pair<UUID, String> generatedRefreshToken = authentication.generateRefreshToken(user.getId(), user.getRole().toString());
            authServiceImplHelper.saveUserRefreshToken(user.getId(), generatedRefreshToken.getFirst());

            return Triple.of(user.getUsername(), generatedAccessToken.getSecond(), generatedRefreshToken.getSecond());
        }
    }
}

// Node: repos/cloned_ms_repos/saigonparking/service/auth-service/src/main/java/com/bht/saigonparking/service/auth/service/impl/AuthServiceImpl.java:AuthServiceImpl.<init>
// Node: getUserByUsername
// Node: getIsActivated
// Node: checkpw
// Node: fork
// Node: WrongPasswordException
// Node: UserNotActivatedException
// Node: WrongUserRoleException
// Node: setUserInfo
// Node: setPassword
// Node: getEmail
// Node: setRole
// Node: setFirstName
// Node: getFirstName
// Node: setLastName
// Node: getLastName
// Node: setPhone
// Node: getPhone
// Node: UserAlreadyActivatedException
// Node: flush
// Node: InvalidRefreshTokenException
// Node: getTime
// Node: setVersion
// Node: getVersion
package com.bht.saigonparking.service.user.mapper;

import javax.persistence.EntityNotFoundException;
import javax.validation.constraints.NotNull;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

import com.bht.saigonparking.api.grpc.user.Customer;
import com.bht.saigonparking.api.grpc.user.User;
import com.bht.saigonparking.api.grpc.user.UserRole;
import com.bht.saigonparking.service.user.entity.CustomerEntity;
import com.bht.saigonparking.service.user.entity.UserEntity;
import com.bht.saigonparking.service.user.repository.core.CustomerRepository;
import com.bht.saigonparking.service.user.repository.core.UserRepository;

import lombok.AllArgsConstructor;

/**
 *
 * @author bht
 */
@Component
@AllArgsConstructor(onConstructor = @__(@Autowired))
public final class UserMapperExtImpl implements UserMapperExt {

    private final EnumMapper enumMapper;
    private final PasswordEncoder passwordEncoder;

    private final UserRepository userRepository;
    private final CustomerRepository customerRepository;

    @Override
    public UserEntity toUserEntity(@NotNull User user, boolean isAboutToCreate) {

        UserEntity userEntity = !isAboutToCreate
                ? userRepository.getByUsername(user.getUsername()).orElseThrow(EntityNotFoundException::new)
                : new UserEntity();

        userEntity.setUsername(user.getUsername());
        userEntity.setUserRoleEntity(enumMapper.toUserRoleEntity(user.getRole()));
        userEntity.setPassword(passwordEncoder.encode(user.getPassword()));
        userEntity.setEmail(user.getEmail());
        userEntity.setIsActivated(user.getIsActivated());

        /* Optimistic version control - prevent loss update */
        userEntity.setVersion(!isAboutToCreate ? user.getVersion() : 1L);
        return userEntity;
    }

    @Override
    public CustomerEntity toCustomerEntity(@NotNull Customer customer, boolean isAboutToCreate) {

        User userInfo = customer.getUserInfo();
        CustomerEntity customerEntity = !isAboutToCreate
                ? customerRepository.getByUsername(userInfo.getUsername()).orElseThrow(EntityNotFoundException::new)
                : new CustomerEntity();

        customerEntity.setUsername(userInfo.getUsername());
        customerEntity.setUserRoleEntity(enumMapper.toUserRoleEntity(UserRole.CUSTOMER));
        customerEntity.setPassword(isAboutToCreate ? passwordEncoder.encode(userInfo.getPassword()) : customerEntity.getPassword());
        customerEntity.setEmail(userInfo.getEmail());
        customerEntity.setFirstName(customer.getFirstName());
        customerEntity.setLastName(customer.getLastName());
        customerEntity.setPhone(customer.getPhone());

        /* Optimistic version control - prevent loss update */
        customerEntity.setVersion(!isAboutToCreate ? userInfo.getVersion() : 1L);
        return customerEntity;
    }
}

// Node: toUserEntity
// Node: UserEntity
// Node: setUserRoleEntity
// Node: toCustomerEntity
// Node: CustomerEntity
package com.bht.saigonparking.service.user.mapper;

import javax.validation.constraints.NotNull;

import com.bht.saigonparking.api.grpc.user.Customer;
import com.bht.saigonparking.api.grpc.user.User;
import com.bht.saigonparking.service.user.entity.CustomerEntity;
import com.bht.saigonparking.service.user.entity.UserEntity;

/**
 *
 * @author bht
 */
public interface UserMapperExt {

    UserEntity toUserEntity(@NotNull User user, boolean isAboutToCreate);

    CustomerEntity toCustomerEntity(@NotNull Customer customer, boolean isAboutToCreate);
}

// Node: repos/cloned_ms_repos/saigonparking/service/user-service/src/main/java/com/bht/saigonparking/service/user/mapper/UserMapperExt.java:UserMapperExt.<init>
// Node: updateUserPassword
package com.bht.saigonparking.service.user.service.main.impl;

import java.sql.Timestamp;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

import javax.persistence.EntityNotFoundException;
import javax.validation.constraints.Max;
import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.bht.saigonparking.common.base.BaseEntity;
import com.bht.saigonparking.service.user.entity.CustomerEntity;
import com.bht.saigonparking.service.user.entity.UserEntity;
import com.bht.saigonparking.service.user.entity.UserRoleEntity;
import com.bht.saigonparking.service.user.mapper.EnumMapper;
import com.bht.saigonparking.service.user.repository.core.CustomerRepository;
import com.bht.saigonparking.service.user.repository.core.UserRepository;
import com.bht.saigonparking.service.user.service.main.UserService;

import lombok.AllArgsConstructor;

/**
 *
 * this class implements all services relevant to User
 *
 * for clean code purpose,
 * using {@code @AllArgsConstructor} for Service class
 * it will {@code @Autowired} all attributes declared inside
 * hide {@code @Autowired} as much as possible in code
 * remember to mark all attributes as {@code private final}
 *
 * @author bht
 */
@Service
@Transactional
@AllArgsConstructor(onConstructor = @__(@Autowired))
public class UserServiceImpl implements UserService {

    private final EnumMapper enumMapper;
    private final PasswordEncoder passwordEncoder;
    private final UserRepository userRepository;
    private final CustomerRepository customerRepository;

    @Override
    public Long countAll(@NotEmpty String keyword, boolean inactivatedOnly) {

        if (keyword.isEmpty()) {
            if (inactivatedOnly) { /* count all inactivated */
                return userRepository.countAll(false);
            } else { /* count all */
                return userRepository.countAll();
            }

        } else {
            if (inactivatedOnly) { /* count all with keyword, inactivated */
                return userRepository.countAll(keyword, false);
            } else { /* count all with keyword */
                return userRepository.countAll(keyword);
            }
        }
    }

    @Override
    public Long countAll(@NotEmpty String keyword, boolean inactivatedOnly, @NotNull UserRoleEntity userRoleEntity) {

        if (keyword.isEmpty()) {
            if (inactivatedOnly) { /* count all by role, inactivated */
                return userRepository.countAll(userRoleEntity, false);
            } else { /* count all by role */
                return userRepository.countAll(userRoleEntity);
            }

        } else {
            if (inactivatedOnly) { /* count all by role, with keyword, inactivated */
                return userRepository.countAll(keyword, userRoleEntity, false);
            } else { /* count all by role, with keyword */
                return userRepository.countAll(keyword, userRoleEntity);
            }
        }
    }

    @Override
    public List<UserEntity> getAll(@NotNull Set<Long> userIdSet) {
        return userIdSet.isEmpty()
                ? Collections.emptyList()
                : userRepository.getAll(userIdSet);
    }

    @Override
    public List<UserEntity> getAll(@NotNull @Max(20L) Integer nRow,
                                   @NotNull Integer pageNumber,
                                   @NotEmpty String keyword,
                                   boolean inactivatedOnly) {

        if (keyword.isEmpty()) {
            if (inactivatedOnly) { /* get all inactivated */
                return userRepository.getAll(nRow, pageNumber, false);
            } else { /* get all */
                return userRepository.getAll(nRow, pageNumber);
            }

        } else {
            if (inactivatedOnly) { /* get all with keyword, inactivated */
                return userRepository.getAll(nRow, pageNumber, keyword, false);
            } else { /* get all with keyword */
                return userRepository.getAll(nRow, pageNumber, keyword);
            }
        }
    }

    @Override
    public List<UserEntity> getAll(@NotNull @Max(20L) Integer nRow,
                                   @NotNull Integer pageNumber,
                                   @NotEmpty String keyword,
                                   boolean inactivatedOnly,
                                   @NotNull UserRoleEntity userRoleEntity) {

        if (keyword.isEmpty()) {
            if (inactivatedOnly) { /* get all by role, inactivated */
                return userRepository.getAll(nRow, pageNumber, userRoleEntity, false);
            } else { /* get all by role */
                return userRepository.getAll(nRow, pageNumber, userRoleEntity);
            }

        } else {
            if (inactivatedOnly) { /* get all by role, with keyword, inactivated */
                return userRepository.getAll(nRow, pageNumber, keyword, userRoleEntity, false);
            } else { /* get all by role, with keyword */
                return userRepository.getAll(nRow, pageNumber, keyword, userRoleEntity);
            }
        }
    }

    @Override
    public UserEntity getUserById(@NotNull Long id) {
        return userRepository.findById(id).orElseThrow(EntityNotFoundException::new);
    }

    @Override
    public UserEntity getUserByUsername(@NotEmpty String username) {
        return userRepository.getByUsername(username).orElseThrow(EntityNotFoundException::new);
    }

    @Override
    public CustomerEntity getCustomerById(@NotNull Long id) {
        return customerRepository.findById(id).orElseThrow(EntityNotFoundException::new);
    }

    @Override
    public CustomerEntity getCustomerByUsername(@NotEmpty String username) {
        return customerRepository.getByUsername(username).orElseThrow(EntityNotFoundException::new);
    }

    @Override
    public Long createUser(@NotNull UserEntity userEntity) {
        UserEntity result = userRepository.saveAndFlush(userEntity);
        return result.getId();
    }

    @Override
    public Long createCustomer(@NotNull CustomerEntity customerEntity) {
        CustomerEntity result = customerRepository.saveAndFlush(customerEntity);
        return result.getId();
    }

    @Override
    public void updateCustomer(@NotNull CustomerEntity customerEntity) {
        customerRepository.saveAndFlush(customerEntity);
    }

    @Override
    public void updateUserLastSignIn(@NotNull Long id, @NotNull Long timeInMillis) {
        UserEntity userEntity = getUserById(id);
        userEntity.setLastSignIn(new Timestamp(timeInMillis));
        userRepository.saveAndFlush(userEntity);
    }

    @Override
    public void activateUserWithId(@NotNull Long id) {
        UserEntity userEntity = getUserById(id);
        userEntity.setIsActivated(true);
        userRepository.saveAndFlush(userEntity);
    }

    @Override
    public void deactivateUserWithId(@NotNull Long id) {
        UserEntity userEntity = getUserById(id);
        userEntity.setIsActivated(false);
        userRepository.saveAndFlush(userEntity);
    }

    @Override
    public void updateUserPassword(@NotNull UserEntity userEntity, @NotEmpty String newPassword) {
        userEntity.setPassword(passwordEncoder.encode(newPassword));
        userRepository.saveAndFlush(userEntity);
    }

    @Override
    public void deleteUserById(@NotNull Long userId) {
        userRepository.delete(getUserById(userId));
    }

    @Override
    public void deleteMultiUserById(@NotNull Set<Long> userIdSet) {
        if (!userIdSet.isEmpty()) {
            List<UserEntity> userEntityList = getAll(userIdSet);
            if (!userEntityList.isEmpty()) {
                userRepository.deleteAll(userEntityList);
            }
        }
    }

    @Override
    public Map<Long, String> mapToUsernameMap(@NotNull Set<Long> userIdSet) {
        List<UserEntity> userEntityList = getAll(userIdSet);
        return userEntityList.isEmpty()
                ? Collections.emptyMap()
                : userEntityList.stream().collect(Collectors.toMap(BaseEntity::getId, UserEntity::getUsername));
    }

    @Override
    public Map<Long, Long> countAllUserGroupByRole() {
        return userRepository.countAllUserGroupByRole().stream().collect(Collectors
                .toMap(tuple -> enumMapper.toUserRoleValue(tuple.get(0, Long.class)), tuple -> tuple.get(1, Long.class)));
    }

    @Override
    public boolean checkUsernameAlreadyExist(@NotEmpty String username) {
        return userRepository.countByUsername(username) != 0;
    }

    @Override
    public boolean checkEmailAlreadyExist(@NotEmpty String email) {
        return userRepository.countByEmail(email) != 0;
    }

    @Override
    public String getUsernameOfUser(@NotNull Long userId) {
        return userRepository.getUsernameOfUser(userId).orElse("unknown");
    }
}

