// Cluster 3

// Node: getClass
// Node: log
// Node: getSimpleName
// Node: of
// Node: equals
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

// Node: validateAdmin
// Node: validateUserRole
// Node: validateUser
package com.bht.saigonparking.common.custom;

import java.lang.reflect.Method;

import org.apache.logging.log4j.Level;
import org.springframework.aop.interceptor.AsyncUncaughtExceptionHandler;
import org.springframework.lang.NonNull;

import com.bht.saigonparking.common.util.LoggingUtil;

/**
 *
 * @author bht
 */
public final class CustomAsyncExceptionHandler implements AsyncUncaughtExceptionHandler {

    @Override
    public void handleUncaughtException(@NonNull Throwable throwable,
                                        @NonNull Method method,
                                        @NonNull Object... objects) {

        LoggingUtil.log(Level.ERROR, "CustomAsyncExceptionHandler", "Exception",
                String.format("Method: %s, Exception: %s", method.getName(), throwable.getClass().getSimpleName()));
    }
}

// Node: repos/cloned_ms_repos/saigonparking/common/src/main/java/com/bht/saigonparking/common/custom/CustomAsyncExceptionHandler.java:CustomAsyncExceptionHandler.<init>
// Node: handleUncaughtException
// Node: format
package com.bht.saigonparking.common.util;

import org.apache.logging.log4j.Level;

import lombok.extern.log4j.Log4j2;

/**
 *
 * @author bht
 */
@Log4j2
public final class LoggingUtil {

    private LoggingUtil() {
    }

    public static void log(Level logLevel, String key, String description, String value) {
        log.log(logLevel, format(key, description, value));
    }

    private static String format(String key, String description, String value) {
        return String.format("%-10s %-14s %s",
                "[" + key + "]",
                description + ":",
                value);
    }
}

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

// Node: onNext
// Node: onCompleted
// Node: getValue
// Node: onError
// Node: getUsername
// Node: newBuilder
// Node: getUserIdContext
package com.bht.saigonparking.service.auth.service.impl;

import static com.bht.saigonparking.common.constant.SaigonParkingMessageQueue.MAIL_TOPIC_ROUTING_KEY;
import static com.bht.saigonparking.common.constant.SaigonParkingMessageQueue.USER_TOPIC_ROUTING_KEY;

import java.util.UUID;

import javax.persistence.EntityNotFoundException;
import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;

import org.apache.logging.log4j.Level;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import com.bht.saigonparking.api.grpc.mail.MailRequest;
import com.bht.saigonparking.api.grpc.mail.MailRequestType;
import com.bht.saigonparking.api.grpc.user.UpdateUserLastSignInRequest;
import com.bht.saigonparking.api.grpc.user.UserServiceGrpc;
import com.bht.saigonparking.common.util.LoggingUtil;
import com.bht.saigonparking.service.auth.entity.UserTokenEntity;
import com.bht.saigonparking.service.auth.repository.UserTokenRepository;
import com.google.protobuf.Empty;
import com.google.protobuf.Int64Value;

import io.grpc.stub.StreamObserver;
import lombok.AllArgsConstructor;

/**
 *
 * @author bht
 */
@Async
@Service
@AllArgsConstructor(onConstructor = @__(@Autowired))
public class AuthServiceHelperImpl {

    private final UserTokenRepository userTokenRepository;
    private final RabbitTemplate rabbitTemplate;
    private final UserServiceGrpc.UserServiceStub userServiceStub;

    public void updateUserLastSignIn(@NotNull Long userId) {
        rabbitTemplate.convertAndSend(USER_TOPIC_ROUTING_KEY, UpdateUserLastSignInRequest.newBuilder()
                .setUserId(userId)
                .setTimeInMillis(System.currentTimeMillis())
                .build());
    }

    public void activateUserWithId(@NotNull Long userId) {
        userServiceStub.activateUser(Int64Value.of(userId), new StreamObserver<Empty>() {
            @Override
            public void onNext(Empty empty) {
                LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                        String.format("activateUserWithId(%d)", userId));
            }

            @Override
            public void onError(Throwable e) {
                LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", e.getMessage());
            }

            @Override
            public void onCompleted() {
                // finish request
            }
        });
    }

    public void sendMail(@NotNull MailRequestType type,
                         @NotEmpty String email,
                         @NotEmpty String username,
                         @NotEmpty String temporaryToken) {

        rabbitTemplate.convertAndSend(MAIL_TOPIC_ROUTING_KEY, MailRequest.newBuilder()
                .setType(type)
                .setEmail(email)
                .setUsername(username)
                .setTemporaryToken(temporaryToken)
                .build());
    }

    public void saveUserRefreshToken(@NotNull Long userId, @NotEmpty UUID tokenId) {
        try {
            /* update refresh token id to database if already existed */
            UserTokenEntity userTokenEntity = userTokenRepository.findById(userId).orElseThrow(EntityNotFoundException::new);
            userTokenEntity.setTokenId(tokenId);
            userTokenRepository.saveAndFlush(userTokenEntity);

        } catch (EntityNotFoundException entityNotFoundException) {
            /* save new refresh token id to database if not existed before */
            UserTokenEntity userTokenEntity = UserTokenEntity.builder().userId(userId).tokenId(tokenId).build();
            userTokenRepository.saveAndFlush(userTokenEntity);

        } finally {
            LoggingUtil.log(Level.INFO, "SERVICE", "Success", String.format("saveUserRefreshToken(%d, %s)", userId, tokenId));
        }
    }
}

// Node: toParkingLot
// Node: toParkingLotResultListWithoutName
// Node: toParkingLotResultListWithName
// Node: toParkingLotList
// Node: getDefaultInstance
// Node: getInformation
// Node: getLatitude
// Node: getLongitude
package com.bht.saigonparking.service.parkinglot.service.grpc;

import java.util.Arrays;
import java.util.HashSet;
import java.util.List;

import org.apache.logging.log4j.Level;
import org.lognet.springboot.grpc.GRpcService;
import org.springframework.beans.factory.annotation.Autowired;

import com.bht.saigonparking.api.grpc.parkinglot.AddEmployeeOfParkingLotRequest;
import com.bht.saigonparking.api.grpc.parkinglot.CountAllParkingLotGroupByTypeResponse;
import com.bht.saigonparking.api.grpc.parkinglot.CountAllParkingLotRequest;
import com.bht.saigonparking.api.grpc.parkinglot.DeleteMultiParkingLotByIdRequest;
import com.bht.saigonparking.api.grpc.parkinglot.GetAllParkingLotRequest;
import com.bht.saigonparking.api.grpc.parkinglot.GetAllParkingLotResponse;
import com.bht.saigonparking.api.grpc.parkinglot.GetEmployeeManageParkingLotIdListResponse;
import com.bht.saigonparking.api.grpc.parkinglot.MapToParkingLotNameMapRequest;
import com.bht.saigonparking.api.grpc.parkinglot.MapToParkingLotNameMapResponse;
import com.bht.saigonparking.api.grpc.parkinglot.ParkingLot;
import com.bht.saigonparking.api.grpc.parkinglot.ParkingLotIdList;
import com.bht.saigonparking.api.grpc.parkinglot.ParkingLotLimit;
import com.bht.saigonparking.api.grpc.parkinglot.ParkingLotResult;
import com.bht.saigonparking.api.grpc.parkinglot.ParkingLotResultList;
import com.bht.saigonparking.api.grpc.parkinglot.ParkingLotServiceGrpc.ParkingLotServiceImplBase;
import com.bht.saigonparking.api.grpc.parkinglot.ParkingLotType;
import com.bht.saigonparking.api.grpc.parkinglot.RemoveEmployeeOfParkingLotRequest;
import com.bht.saigonparking.api.grpc.parkinglot.ScanningByRadiusRequest;
import com.bht.saigonparking.api.grpc.parkinglot.UpdateParkingLotAvailabilityRequest;
import com.bht.saigonparking.common.interceptor.SaigonParkingServerInterceptor;
import com.bht.saigonparking.common.util.LoggingUtil;
import com.bht.saigonparking.service.parkinglot.entity.ParkingLotLimitEntity;
import com.bht.saigonparking.service.parkinglot.mapper.EnumMapper;
import com.bht.saigonparking.service.parkinglot.mapper.ParkingLotMapper;
import com.bht.saigonparking.service.parkinglot.mapper.ParkingLotMapperExt;
import com.bht.saigonparking.service.parkinglot.service.main.ParkingLotService;
import com.google.protobuf.BoolValue;
import com.google.protobuf.Empty;
import com.google.protobuf.Int64Value;
import com.google.protobuf.StringValue;

import io.grpc.stub.StreamObserver;
import lombok.AllArgsConstructor;

/**
 *
 * this class implements all services of ParkingLotStub
 *
 * for clean code purpose,
 * using {@code @AllArgsConstructor} for Service class
 * it will {@code @Autowired} all attributes declared inside
 * hide {@code @Autowired} as much as possible in code
 * remember to mark all attributes as {@code private final}
 *
 * @author bht
 */
@GRpcService
@AllArgsConstructor(onConstructor = @__(@Autowired))
public final class ParkingLotServiceGrpcImpl extends ParkingLotServiceImplBase {

    private final ParkingLotService parkingLotService;
    private final ParkingLotMapper parkingLotMapper;
    private final ParkingLotMapperExt parkingLotMapperExt;
    private final EnumMapper enumMapper;
    private final SaigonParkingServerInterceptor serverInterceptor;

    @Override
    public void getParkingLotIdByAuthorizationHeader(Empty request, StreamObserver<Int64Value> responseObserver) {
        try {
            serverInterceptor.validateUserRole("PARKING_LOT_EMPLOYEE");

            long employeeId = serverInterceptor.getUserIdContext().get();
            long parkingLotId = parkingLotService.getParkingLotIdByParkingLotEmployeeId(employeeId);

            responseObserver.onNext(Int64Value.of(parkingLotId));
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("getParkingLotIdByAuthorizationHeader(%d): %d", employeeId, parkingLotId));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL", "getParkingLotIdByAuthorizationHeader()");
        }
    }

    @Override
    public void getParkingLotIdByParkingLotEmployeeId(Int64Value request, StreamObserver<Int64Value> responseObserver) {
        try {
            serverInterceptor.validateAdmin();

            long employeeId = request.getValue();
            long parkingLotId = parkingLotService.getParkingLotIdByParkingLotEmployeeId(employeeId);

            responseObserver.onNext(Int64Value.of(parkingLotId));
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("getParkingLotIdByParkingLotEmployeeId(%d): %d", employeeId, parkingLotId));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("getParkingLotIdByParkingLotEmployeeId(%d)", request.getValue()));
        }
    }

    @Override
    public void countAllParkingLot(CountAllParkingLotRequest request, StreamObserver<Int64Value> responseObserver) {
        try {
            serverInterceptor.validateAdmin();

            Long count;

            if (request.getParkingLotType().equals(ParkingLotType.ALL)) {
                count = parkingLotService.countAll(request.getKeyword(), request.getAvailableOnly());

            } else {
                count = parkingLotService.countAll(request.getKeyword(), request.getAvailableOnly(),
                        enumMapper.toParkingLotTypeEntity(request.getParkingLotType()));
            }

            responseObserver.onNext(Int64Value.of(count));
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("countAllParkingLot(%s, %b, %s): %d",
                            request.getKeyword(), request.getAvailableOnly(), request.getParkingLotType(), count));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("countAllParkingLot(%s, %b, %s)",
                            request.getKeyword(), request.getAvailableOnly(), request.getParkingLotType()));
        }
    }

    @Override
    public void getAllParkingLot(GetAllParkingLotRequest request, StreamObserver<GetAllParkingLotResponse> responseObserver) {
        try {
            serverInterceptor.validateAdmin();

            List<ParkingLot> parkingLotList;

            if (request.getParkingLotType().equals(ParkingLotType.ALL)) {
                parkingLotList = parkingLotMapper.toParkingLotList(parkingLotService
                        .getAll(request.getNRow(), request.getPageNumber(), request.getKeyword(), request.getAvailableOnly()));

            } else {
                parkingLotList = parkingLotMapper.toParkingLotList(parkingLotService
                        .getAll(request.getNRow(), request.getPageNumber(), request.getKeyword(), request.getAvailableOnly(),
                                enumMapper.toParkingLotTypeEntity(request.getParkingLotType())));
            }

            responseObserver.onNext(GetAllParkingLotResponse.newBuilder().addAllParkingLot(parkingLotList).build());
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("getAllParkingLot(%s, %b, %s, %d, %d)",
                            request.getKeyword(), request.getAvailableOnly(), request.getParkingLotType(), request.getNRow(), request.getPageNumber()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("getAllParkingLot(%s, %b, %s, %d, %d)",
                            request.getKeyword(), request.getAvailableOnly(), request.getParkingLotType(), request.getNRow(), request.getPageNumber()));
        }
    }

    @Override
    public void getParkingLotById(Int64Value request, StreamObserver<ParkingLot> responseObserver) {
        try {
            ParkingLot parkingLot = parkingLotMapper.toParkingLot(
                    parkingLotService.getParkingLotById(request.getValue()));

            responseObserver.onNext(parkingLot);
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("getParkingLotById(%d)", request.getValue()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("getParkingLotById(%d)", request.getValue()));
        }
    }

    @Override
    public void checkLimit(Int64Value request, StreamObserver<ParkingLotLimit> responseObserver) {
        try {
            ParkingLotLimitEntity parkingLotLimitEntity = parkingLotService.getParkingLotLimitById(request.getValue());
            ParkingLotLimit parkingLotLimit = ParkingLotLimit.newBuilder()
                    .setAvailableSlot(parkingLotLimitEntity.getAvailableSlot())
                    .setTotalSlot(parkingLotLimitEntity.getTotalSlot())
                    .build();

            responseObserver.onNext(parkingLotLimit);
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("checkLimit(%d): %d/%d",
                            request.getValue(), parkingLotLimitEntity.getAvailableSlot(), parkingLotLimitEntity.getTotalSlot()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("checkLimit(%d)", request.getValue()));
        }
    }

    @Override
    public void checkAvailability(Int64Value request, StreamObserver<BoolValue> responseObserver) {
        try {
            BoolValue boolValue = BoolValue.newBuilder()
                    .setValue(parkingLotService.checkAvailability(request.getValue()))
                    .build();

            responseObserver.onNext(boolValue);
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("checkAvailability(%d): %s", request.getValue(), boolValue.getValue()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("checkAvailability(%d)", request.getValue()));
        }
    }

    @Override
    public void checkUnavailability(ParkingLotIdList request, StreamObserver<ParkingLotIdList> responseObserver) {
        try {
            ParkingLotIdList parkingLotIdList = ParkingLotIdList.newBuilder()
                    .addAllParkingLotId(parkingLotService.checkUnavailability(request.getParkingLotIdList()))
                    .build();

            responseObserver.onNext(parkingLotIdList);
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("checkUnavailability of %d parking-lot", request.getParkingLotIdCount()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("checkUnavailability of %d parking-lot", request.getParkingLotIdCount()));
        }
    }

    @Override
    public void getTopParkingLotInRegionOrderByDistanceWithName(ScanningByRadiusRequest request, StreamObserver<ParkingLotResultList> responseObserver) {
        try {
            List<ParkingLotResult> parkingLotResultList = parkingLotMapper.toParkingLotResultListWithName(
                    parkingLotService.getTopParkingLotInRegionOrderByDistanceWithName(
                            request.getLatitude(),
                            request.getLongitude(),
                            request.getRadiusToScan(),
                            request.getNResult()));

            responseObserver.onNext(ParkingLotResultList.newBuilder().addAllParkingLotResult(parkingLotResultList).build());
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("getTopParkingLotInRegionOrderByDistanceWithName(%f, %f, %d, %d)",
                            request.getLatitude(), request.getLongitude(), request.getRadiusToScan(), request.getNResult()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("getTopParkingLotInRegionOrderByDistanceWithName(%f, %f, %d, %d)",
                            request.getLatitude(), request.getLongitude(), request.getRadiusToScan(), request.getNResult()));
        }
    }

    @Override
    public void getTopParkingLotInRegionOrderByDistanceWithoutName(ScanningByRadiusRequest request, StreamObserver<ParkingLotResultList> responseObserver) {
        try {
            List<ParkingLotResult> parkingLotResultList = parkingLotMapper.toParkingLotResultListWithoutName(
                    parkingLotService.getTopParkingLotInRegionOrderByDistanceWithoutName(
                            request.getLatitude(),
                            request.getLongitude(),
                            request.getRadiusToScan(),
                            request.getNResult()));

            responseObserver.onNext(ParkingLotResultList.newBuilder().addAllParkingLotResult(parkingLotResultList).build());
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("getTopParkingLotInRegionOrderByDistanceWithoutName(%f, %f, %d, %d)",
                            request.getLatitude(), request.getLongitude(), request.getRadiusToScan(), request.getNResult()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("getTopParkingLotInRegionOrderByDistanceWithoutName(%f, %f, %d, %d)",
                            request.getLatitude(), request.getLongitude(), request.getRadiusToScan(), request.getNResult()));
        }
    }

    @Override
    public void deleteParkingLotById(Int64Value request, StreamObserver<Empty> responseObserver) {
        try {
            serverInterceptor.validateAdmin();

            parkingLotService.deleteParkingLotById(request.getValue());

            responseObserver.onNext(Empty.getDefaultInstance());
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("deleteParkingLotById(%d)", request.getValue()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("deleteParkingLotById(%d)", request.getValue()));
        }
    }

    @Override
    public void deleteMultiParkingLotById(DeleteMultiParkingLotByIdRequest request, StreamObserver<Empty> responseObserver) {
        try {
            serverInterceptor.validateAdmin();

            parkingLotService.deleteMultiParkingLotById(new HashSet<>(request.getParkingLotIdList()));

            responseObserver.onNext(Empty.getDefaultInstance());
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("deleteMultiParkingLotById(%s)", request.getParkingLotIdList()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("deleteMultiParkingLotById(%s)", request.getParkingLotIdList()));
        }
    }

    @Override
    public void updateParkingLotAvailability(UpdateParkingLotAvailabilityRequest request, StreamObserver<Empty> responseObserver) {
        try {
            serverInterceptor.validateUserRole(Arrays.asList("PARKING_LOT_EMPLOYEE", "ADMIN"));

            parkingLotService.updateAvailability((short) request.getNewAvailability(), request.getParkingLotId());

            responseObserver.onNext(Empty.getDefaultInstance());
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("updateParkingLotAvailability(%d): %d", request.getParkingLotId(), request.getNewAvailability()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("updateParkingLotAvailability(%d): %d", request.getParkingLotId(), request.getNewAvailability()));
        }
    }

    @Override
    public void mapToParkingLotNameMap(MapToParkingLotNameMapRequest request, StreamObserver<MapToParkingLotNameMapResponse> responseObserver) {
        try {
            serverInterceptor.validateAdmin();

            MapToParkingLotNameMapResponse mapToParkingLotNameMapResponse = MapToParkingLotNameMapResponse.newBuilder()
                    .putAllParkingLotName(parkingLotService.mapToParkingLotNameMap(new HashSet<>(request.getParkingLotIdList())))
                    .build();

            responseObserver.onNext(mapToParkingLotNameMapResponse);
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success", "mapToParkingLotNameMap()");

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL", "mapToParkingLotNameMap()");
        }
    }

    @Override
    public void getParkingLotNameByParkingLotId(Int64Value request, StreamObserver<StringValue> responseObserver) {
        try {
            serverInterceptor.validateAdmin();

            String parkingLotName = parkingLotService.getParkingLotNameByParkingLotId(request.getValue());

            responseObserver.onNext(StringValue.of(parkingLotName));
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("getParkingLotNameByParkingLotId(%d): %s", request.getValue(), parkingLotName));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("getParkingLotNameByParkingLotId(%d)", request.getValue()));
        }
    }

    @Override
    public void countAllParkingLotGroupByType(Empty request, StreamObserver<CountAllParkingLotGroupByTypeResponse> responseObserver) {
        try {
            serverInterceptor.validateAdmin();

            CountAllParkingLotGroupByTypeResponse response = CountAllParkingLotGroupByTypeResponse.newBuilder()
                    .putAllTypeCount(parkingLotService.countAllParkingLotGroupByType())
                    .build();

            responseObserver.onNext(response);
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success", "countAllParkingLotGroupByType()");

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL", "countAllParkingLotGroupByType()");
        }
    }

    @Override
    public void addEmployeeOfParkingLot(AddEmployeeOfParkingLotRequest request, StreamObserver<Empty> responseObserver) {
        try {
            serverInterceptor.validateAdmin();
            parkingLotService.addEmployeeOfParkingLot(request.getEmployeeId(), request.getParkingLotId());

            responseObserver.onNext(Empty.getDefaultInstance());
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("addEmployeeOfParkingLot(%d, %d)", request.getEmployeeId(), request.getParkingLotId()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("addEmployeeOfParkingLot(%d, %d)", request.getEmployeeId(), request.getParkingLotId()));
        }
    }

    @Override
    public void removeEmployeeOfParkingLot(RemoveEmployeeOfParkingLotRequest request, StreamObserver<Empty> responseObserver) {
        try {
            serverInterceptor.validateAdmin();
            parkingLotService.removeEmployeeOfParkingLot(request.getEmployeeId(), request.getParkingLotId(), request.getDeleteEmployee());

            responseObserver.onNext(Empty.getDefaultInstance());
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("removeEmployeeOfParkingLot(%d, %d, %b)",
                            request.getEmployeeId(), request.getParkingLotId(), request.getDeleteEmployee()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("removeEmployeeOfParkingLot(%d, %d, %b)",
                            request.getEmployeeId(), request.getParkingLotId(), request.getDeleteEmployee()));
        }
    }

    @Override
    public void createNewParkingLot(ParkingLot request, StreamObserver<Int64Value> responseObserver) {
        try {
            serverInterceptor.validateAdmin();

            Long newParkingLotId = parkingLotService.createNewParkingLot(
                    parkingLotMapperExt.toParkingLotEntity(request, true),
                    parkingLotMapper.toParkingLotLimitEntityIgnoreParkingLotEntity(request),
                    parkingLotMapper.toParkingLotInformationEntityIgnoreParkingLotEntity(request));

            responseObserver.onNext(Int64Value.of(newParkingLotId));
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("createNewParkingLot(%s)", request.getInformation().getName()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("createNewParkingLot(%s)", request.getInformation().getName()));
        }
    }

    @Override
    public void checkEmployeeAlreadyManageParkingLot(Int64Value request, StreamObserver<BoolValue> responseObserver) {
        try {
            serverInterceptor.validateAdmin();

            boolean isEmployeeAlreadyManageParkingLot = parkingLotService.checkEmployeeAlreadyManageParkingLot(request.getValue());

            responseObserver.onNext(BoolValue.of(isEmployeeAlreadyManageParkingLot));
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("checkEmployeeAlreadyManageParkingLot(%d): %b", request.getValue(), isEmployeeAlreadyManageParkingLot));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("checkEmployeeAlreadyManageParkingLot(%d)", request.getValue()));
        }
    }

    @Override
    public void getEmployeeManageParkingLotIdList(Int64Value request, StreamObserver<GetEmployeeManageParkingLotIdListResponse> responseObserver) {
        try {
            serverInterceptor.validateAdmin();

            List<Long> employeeIdList = parkingLotService.getEmployeeManageParkingLotIdList(request.getValue());
            GetEmployeeManageParkingLotIdListResponse response = GetEmployeeManageParkingLotIdListResponse.newBuilder()
                    .addAllEmployeeId(employeeIdList)
                    .build();

            responseObserver.onNext(response);
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("getEmployeeManageParkingLotIdList(%d): %s", request.getValue(), employeeIdList));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("getEmployeeManageParkingLotIdList(%d)", request.getValue()));
        }
    }

    @Override
    public void getParkingLotManagedByEmployee(Int64Value request, StreamObserver<ParkingLot> responseObserver) {
        try {
            serverInterceptor.validateUserRole(Arrays.asList("PARKING_LOT_EMPLOYEE", "ADMIN"));

            ParkingLot parkingLot = parkingLotMapper.toParkingLot(parkingLotService.getParkingLotByEmployeeId(request.getValue()));

            responseObserver.onNext(parkingLot);
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("getParkingLotManagedByEmployee(%d): %s", request.getValue(), parkingLot.getInformation().getName()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("getParkingLotManagedByEmployee(%d)", request.getValue()));
        }
    }
}

// Node: getParkingLotIdByAuthorizationHeader
// Node: countAllParkingLot
// Node: getParkingLotType
// Node: getKeyword
// Node: getAvailableOnly
// Node: getAllParkingLot
// Node: getNRow
// Node: getPageNumber
// Node: addAllParkingLot
// Node: checkLimit
// Node: setValue
// Node: getParkingLotIdList
// Node: getParkingLotIdCount
// Node: getRadiusToScan
// Node: getNResult
// Node: addAllParkingLotResult
// Node: asList
// Node: getParkingLotId
// Node: putAllParkingLotName
// Node: putAllTypeCount
// Node: getEmployeeId
// Node: getDeleteEmployee
// Node: getParkingLotManagedByEmployee
package com.bht.saigonparking.service.parkinglot.service.extra.impl;

import java.io.IOException;
import java.io.InputStream;

import javax.validation.constraints.NotEmpty;

import org.apache.logging.log4j.Level;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.amazonaws.AmazonClientException;
import com.amazonaws.services.s3.AmazonS3;
import com.amazonaws.services.s3.model.ObjectMetadata;
import com.bht.saigonparking.common.util.LoggingUtil;
import com.bht.saigonparking.service.parkinglot.service.extra.S3Service;
import com.google.common.io.ByteSource;

import lombok.AllArgsConstructor;

/**
 *
 * this class implements all services relevant to amazon S3
 * S3 is a cloud storage approach for web-services, provided by amazon
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
public class S3ServiceImpl implements S3Service {

    private final AmazonS3 amazonS3Client;

    @Qualifier("bucketName")
    private final String bucketName;

    @Override
    public InputStream getFile(@NotEmpty String filePath, boolean warnOnFail) {
        try {

            InputStream inputStream = amazonS3Client.getObject(bucketName, filePath).getObjectContent();
            LoggingUtil.log(Level.DEBUG, "SERVICE", "Success", String.format("getS3File(\"%s\")", filePath));
            return inputStream;

        } catch (AmazonClientException exception) {

            if (warnOnFail) {
                LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
                LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL", String.format("getS3File(\"%s\")", filePath));
            }

            return null;
        }
    }

    @Override
    public void saveFile(byte[] fileData, @NotEmpty String filePath, boolean warnOnFail) {
        try (InputStream inputStream = ByteSource.wrap(fileData).openStream()) {

            ObjectMetadata metadata = new ObjectMetadata();
            metadata.setContentLength(fileData.length);
            amazonS3Client.putObject(bucketName, filePath, inputStream, metadata);

            LoggingUtil.log(Level.DEBUG, "SERVICE", "Success", String.format("saveS3File(\"%s\")", filePath));

        } catch (AmazonClientException | IOException exception) {

            if (warnOnFail) {
                LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
                LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL", String.format("saveS3File(\"%s\")", filePath));
            }
        }
    }

    @Override
    public void deleteFile(@NotEmpty String filePath, boolean warnOnFail) {
        try {
            amazonS3Client.deleteObject(bucketName, filePath);

            LoggingUtil.log(Level.DEBUG, "SERVICE", "Success", String.format("deleteS3File(\"%s\")", filePath));

        } catch (AmazonClientException exception) {

            if (warnOnFail) {
                LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
                LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL", String.format("deleteS3File(\"%s\")", filePath));
            }
        }
    }
}

// Node: deleteObject
// Node: deleteS3File
package com.bht.saigonparking.service.parkinglot.service.main.impl;

import static com.bht.saigonparking.common.constant.SaigonParkingMessageQueue.BOOKING_TOPIC_ROUTING_KEY;
import static com.bht.saigonparking.common.constant.SaigonParkingMessageQueue.PARKING_LOT_TOPIC_ROUTING_KEY;

import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

import javax.persistence.EntityNotFoundException;
import javax.persistence.Tuple;
import javax.validation.constraints.Max;
import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;

import org.apache.logging.log4j.Level;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.bht.saigonparking.api.grpc.booking.BookingStatisticRequest;
import com.bht.saigonparking.api.grpc.booking.BookingStatisticRequestType;
import com.bht.saigonparking.api.grpc.parkinglot.DeleteParkingLotNotification;
import com.bht.saigonparking.api.grpc.parkinglot.ParkingLotEmployeeInfo;
import com.bht.saigonparking.api.grpc.user.UserServiceGrpc;
import com.bht.saigonparking.common.util.LoggingUtil;
import com.bht.saigonparking.service.parkinglot.entity.ParkingLotEmployeeEntity;
import com.bht.saigonparking.service.parkinglot.entity.ParkingLotEntity;
import com.bht.saigonparking.service.parkinglot.entity.ParkingLotInformationEntity;
import com.bht.saigonparking.service.parkinglot.entity.ParkingLotLimitEntity;
import com.bht.saigonparking.service.parkinglot.entity.ParkingLotTypeEntity;
import com.bht.saigonparking.service.parkinglot.mapper.EnumMapper;
import com.bht.saigonparking.service.parkinglot.repository.core.ParkingLotEmployeeRepository;
import com.bht.saigonparking.service.parkinglot.repository.core.ParkingLotInformationRepository;
import com.bht.saigonparking.service.parkinglot.repository.core.ParkingLotLimitRepository;
import com.bht.saigonparking.service.parkinglot.repository.core.ParkingLotRepository;
import com.bht.saigonparking.service.parkinglot.service.main.ParkingLotService;
import com.google.protobuf.Empty;
import com.google.protobuf.Int64Value;

import io.grpc.stub.StreamObserver;
import lombok.AllArgsConstructor;

/**
 *
 * this class implements all services relevant to ParkingLot
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
public class ParkingLotServiceImpl implements ParkingLotService {

    private final EnumMapper enumMapper;
    private final RabbitTemplate rabbitTemplate;
    private final ParkingLotRepository parkingLotRepository;
    private final ParkingLotLimitRepository parkingLotLimitRepository;
    private final ParkingLotEmployeeRepository parkingLotEmployeeRepository;
    private final ParkingLotInformationRepository parkingLotInformationRepository;
    private final UserServiceGrpc.UserServiceStub userServiceStub;

    @Override
    public Long getParkingLotIdByParkingLotEmployeeId(@NotNull Long parkingLotEmployeeId) {
        return parkingLotEmployeeRepository.getParkingLotIdByParkingLotEmployeeId(parkingLotEmployeeId);
    }

    @Override
    public Long countAll(@NotEmpty String keyword, boolean isAvailableOnly) {

        if (keyword.isEmpty()) {
            if (isAvailableOnly) { /* count all available */
                return parkingLotRepository.countAll(true);
            } else { /* count all */
                return parkingLotRepository.countAll();
            }

        } else {
            if (isAvailableOnly) { /* count all with keyword, available */
                return parkingLotRepository.countAll(keyword, true);
            } else { /* count all with keyword */
                return parkingLotRepository.countAll(keyword);
            }
        }
    }

    @Override
    public Long countAll(@NotEmpty String keyword, boolean isAvailableOnly, @NotNull ParkingLotTypeEntity parkingLotTypeEntity) {

        if (keyword.isEmpty()) {
            if (isAvailableOnly) { /* count all by type, available */
                return parkingLotRepository.countAll(parkingLotTypeEntity, true);
            } else { /* count all by type */
                return parkingLotRepository.countAll(parkingLotTypeEntity);
            }

        } else {
            if (isAvailableOnly) { /* count all by type, with keyword, available */
                return parkingLotRepository.countAll(keyword, parkingLotTypeEntity, true);
            } else { /* count all by type, with keyword */
                return parkingLotRepository.countAll(keyword, parkingLotTypeEntity);
            }
        }
    }

    @Override
    public List<ParkingLotEntity> getAll(@NotNull Set<Long> parkingLotIdSet) {
        return parkingLotIdSet.isEmpty()
                ? Collections.emptyList()
                : parkingLotRepository.getAll(parkingLotIdSet);
    }

    @Override
    public List<ParkingLotEntity> getAll(@NotNull @Max(20L) Integer nRow,
                                         @NotNull Integer pageNumber,
                                         @NotEmpty String keyword,
                                         boolean isAvailableOnly) {

        if (keyword.isEmpty()) {
            if (isAvailableOnly) { /* get all available */
                return parkingLotRepository.getAll(nRow, pageNumber, true);
            } else { /* get all */
                return parkingLotRepository.getAll(nRow, pageNumber);
            }

        } else {
            if (isAvailableOnly) { /* get all with keyword, available */
                return parkingLotRepository.getAll(nRow, pageNumber, keyword, true);
            } else { /* get all with keyword */
                return parkingLotRepository.getAll(nRow, pageNumber, keyword);
            }
        }
    }

    @Override
    public List<ParkingLotEntity> getAll(@NotNull @Max(20L) Integer nRow,
                                         @NotNull Integer pageNumber,
                                         @NotEmpty String keyword,
                                         boolean isAvailableOnly,
                                         @NotNull ParkingLotTypeEntity parkingLotTypeEntity) {

        if (keyword.isEmpty()) {
            if (isAvailableOnly) { /* get all by type, available */
                return parkingLotRepository.getAll(nRow, pageNumber, parkingLotTypeEntity, true);
            } else { /* get all by type */
                return parkingLotRepository.getAll(nRow, pageNumber, parkingLotTypeEntity);
            }

        } else {
            if (isAvailableOnly) { /* get all by type, with keyword, available */
                return parkingLotRepository.getAll(nRow, pageNumber, keyword, parkingLotTypeEntity, true);
            } else { /* get all by type, with keyword */
                return parkingLotRepository.getAll(nRow, pageNumber, keyword, parkingLotTypeEntity);
            }
        }
    }

    @Override
    public ParkingLotEntity getParkingLotById(@NotNull Long id) {
        return parkingLotRepository.findById(id).orElseThrow(EntityNotFoundException::new);
    }

    @Override
    public ParkingLotEntity getParkingLotByEmployeeId(@NotNull Long parkingLotEmployeeId) {
        return parkingLotRepository.getByEmployeeId(parkingLotEmployeeId).orElseThrow(EntityNotFoundException::new);
    }

    @Override
    public ParkingLotLimitEntity getParkingLotLimitById(@NotNull Long id) {
        return parkingLotLimitRepository.findById(id).orElseThrow(EntityNotFoundException::new);
    }

    @Override
    public Boolean checkAvailability(@NotNull Long parkingLotId) {
        return parkingLotRepository.checkAvailability(parkingLotId);
    }

    @Override
    public List<Long> checkUnavailability(@NotEmpty List<Long> parkingLotIdList) {
        return parkingLotRepository.checkUnavailability(parkingLotIdList);
    }

    @Override
    public List<Tuple> getTopParkingLotInRegionOrderByDistanceWithoutName(@NotNull Double lat,
                                                                          @NotNull Double lng,
                                                                          @NotNull Integer radius,
                                                                          @NotNull Integer nResult) {
        return parkingLotRepository.getTopParkingLotInRegionOrderByDistanceWithoutName(lat, lng, radius, nResult);
    }

    @Override
    public List<Tuple> getTopParkingLotInRegionOrderByDistanceWithName(@NotNull Double lat,
                                                                       @NotNull Double lng,
                                                                       @NotNull Integer radius,
                                                                       @NotNull Integer nResult) {
        return parkingLotRepository.getTopParkingLotInRegionOrderByDistanceWithName(lat, lng, radius, nResult);
    }

    @Override
    public void deleteParkingLotById(@NotNull Long parkingLotId) {
        ParkingLotEntity parkingLotEntity = getParkingLotById(parkingLotId);
        Set<Long> employeeIdSet = parkingLotEntity.getParkingLotEmployeeEntitySet().stream()
                .map(ParkingLotEmployeeEntity::getUserId)
                .collect(Collectors.toSet());

        parkingLotRepository.delete(parkingLotEntity);

        rabbitTemplate.convertAndSend(PARKING_LOT_TOPIC_ROUTING_KEY, DeleteParkingLotNotification.newBuilder()
                .addAllInfo(Collections
                        .singleton(ParkingLotEmployeeInfo.newBuilder()
                                .setParkingLotId(parkingLotId)
                                .addAllEmployeeId(employeeIdSet)
                                .build()))
                .build());

        rabbitTemplate.convertAndSend(BOOKING_TOPIC_ROUTING_KEY, BookingStatisticRequest.newBuilder()
                .setType(BookingStatisticRequestType.DELETE)
                .addAllParkingLotId(Collections.singleton(parkingLotId))
                .build());
    }

    @Override
    public void deleteMultiParkingLotById(@NotNull Set<Long> parkingLotIdSet) {
        if (!parkingLotIdSet.isEmpty()) {
            List<ParkingLotEntity> parkingLotEntityList = getAll(parkingLotIdSet);
            if (!parkingLotEntityList.isEmpty()) {

                Set<ParkingLotEmployeeInfo> parkingLotEmployeeInfoSet = parkingLotEntityList.stream()
                        .map(parkingLotEntity -> ParkingLotEmployeeInfo.newBuilder()
                                .setParkingLotId(parkingLotEntity.getId())
                                .addAllEmployeeId(parkingLotEntity.getParkingLotEmployeeEntitySet().stream()
                                        .map(ParkingLotEmployeeEntity::getUserId)
                                        .collect(Collectors.toSet()))
                                .build())
                        .collect(Collectors.toSet());

                parkingLotRepository.deleteAll(parkingLotEntityList);

                rabbitTemplate.convertAndSend(PARKING_LOT_TOPIC_ROUTING_KEY, DeleteParkingLotNotification.newBuilder()
                        .addAllInfo(parkingLotEmployeeInfoSet)
                        .build());

                rabbitTemplate.convertAndSend(BOOKING_TOPIC_ROUTING_KEY, BookingStatisticRequest.newBuilder()
                        .setType(BookingStatisticRequestType.DELETE)
                        .addAllParkingLotId(parkingLotIdSet)
                        .build());
            }
        }
    }

    @Override
    public void updateAvailability(@NotNull Short newAvailability, @NotNull Long parkingLotId) {
        parkingLotLimitRepository.updateAvailability(newAvailability, parkingLotId);
    }

    @Override
    public Map<Long, String> mapToParkingLotNameMap(@NotNull Set<Long> parkingLotIdSet) {
        return parkingLotInformationRepository
                .mapParkingLotNameWithId(parkingLotIdSet).stream()
                .collect(Collectors.toMap(tuple -> tuple.get(0, Long.class), tuple -> tuple.get(1, String.class)));
    }

    @Override
    public Map<Long, Long> countAllParkingLotGroupByType() {
        return parkingLotRepository.countAllParkingLotGroupByType().stream().collect(Collectors
                .toMap(tuple -> enumMapper.toParkingLotTypeValue(tuple.get(0, Long.class)), tuple -> tuple.get(1, Long.class)));
    }

    @Override
    public String getParkingLotNameByParkingLotId(@NotNull Long parkingLotId) {
        return parkingLotInformationRepository.getParkingLotName(parkingLotId).orElseThrow(EntityNotFoundException::new);
    }

    @Override
    public Long createNewParkingLot(@NotNull ParkingLotEntity parkingLotEntity,
                                    @NotNull ParkingLotLimitEntity parkingLotLimitEntity,
                                    @NotNull ParkingLotInformationEntity parkingLotInformationEntity) {

        ParkingLotEntity result = parkingLotRepository.saveAndFlush(parkingLotEntity);

        parkingLotLimitEntity.setParkingLotEntity(result);
        parkingLotLimitRepository.saveAndFlush(parkingLotLimitEntity);

        parkingLotInformationEntity.setParkingLotEntity(result);
        parkingLotInformationRepository.saveAndFlush(parkingLotInformationEntity);

        rabbitTemplate.convertAndSend(BOOKING_TOPIC_ROUTING_KEY, BookingStatisticRequest.newBuilder()
                .setType(BookingStatisticRequestType.CREATE)
                .addAllParkingLotId(Collections.singleton(result.getId()))
                .build());

        return result.getId();
    }

    @Override
    public boolean checkEmployeeAlreadyManageParkingLot(@NotNull Long employeeId) {
        return parkingLotEmployeeRepository.countByUserId(employeeId) != 0;
    }

    @Override
    public List<Long> getEmployeeManageParkingLotIdList(@NotNull Long parkingLotId) {
        return parkingLotEmployeeRepository.getEmployeeManageParkingLotIdList(parkingLotId);
    }

    @Override
    public void addEmployeeOfParkingLot(@NotNull Long employeeId, @NotNull Long parkingLotId) {
        ParkingLotEntity parkingLotEntity = getParkingLotById(parkingLotId);
        ParkingLotEmployeeEntity parkingLotEmployeeEntity = ParkingLotEmployeeEntity.builder()
                .userId(employeeId)
                .parkingLotEntity(parkingLotEntity)
                .build();

        parkingLotEmployeeRepository.saveAndFlush(parkingLotEmployeeEntity);
    }

    @Async
    @Override
    public void removeEmployeeOfParkingLot(@NotNull Long employeeId, @NotNull Long parkingLotId, boolean deleteEmployee) {
        ParkingLotEmployeeEntity parkingLotEmployeeEntity = parkingLotEmployeeRepository
                .getByEmployeeId(employeeId).orElseThrow(EntityNotFoundException::new);

        parkingLotEmployeeRepository.delete(parkingLotEmployeeEntity);

        if (deleteEmployee) {
            userServiceStub.deleteUserById(Int64Value.of(employeeId), new StreamObserver<Empty>() {
                @Override
                public void onNext(Empty empty) {
                    // ...
                }

                @Override
                public void onError(Throwable throwable) {
                    LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", throwable.getClass().getSimpleName());
                    LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                            String.format("deleteEmployeeById(%d)", employeeId));
                }

                @Override
                public void onCompleted() {
                    LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                            String.format("deleteEmployeeById(%d)", employeeId));
                }
            });
        }
    }
}

// Node: deleteEmployeeById
package com.bht.saigonparking.service.user.configuration;

import static com.bht.saigonparking.common.constant.SaigonParkingMessageQueue.PARKING_LOT_QUEUE_NAME;
import static com.bht.saigonparking.common.constant.SaigonParkingMessageQueue.USER_QUEUE_NAME;

import java.util.HashSet;
import java.util.stream.Collectors;

import javax.transaction.Transactional;

import org.apache.logging.log4j.Level;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.bht.saigonparking.api.grpc.parkinglot.DeleteParkingLotNotification;
import com.bht.saigonparking.api.grpc.parkinglot.ParkingLotEmployeeInfo;
import com.bht.saigonparking.api.grpc.user.UpdateUserLastSignInRequest;
import com.bht.saigonparking.common.util.LoggingUtil;
import com.bht.saigonparking.service.user.service.main.UserService;

import lombok.AllArgsConstructor;

/**
 *
 * @author bht
 */
@Service
@Transactional
@AllArgsConstructor(onConstructor = @__(@Autowired))
public class MessageQueueConfiguration {

    private final UserService userService;

    @RabbitListener(queues = {USER_QUEUE_NAME})
    public void consumeMessageFromUserTopic(UpdateUserLastSignInRequest request) {
        try {
            userService.updateUserLastSignIn(request.getUserId(), request.getTimeInMillis());
            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("updateUserLastSignIn(%d)", request.getUserId()));

        } catch (Exception exception) {

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("updateUserLastSignIn(%d)", request.getUserId()));
        }
    }

    @RabbitListener(queues = {PARKING_LOT_QUEUE_NAME})
    public void consumeMessageFromParkingLotTopic(DeleteParkingLotNotification notification) {
        try {
            notification.getInfoList().forEach(info -> {
                userService.deleteMultiUserById(new HashSet<>(info.getEmployeeIdList()));
                LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                        String.format("deleteParkingLotEmployeesByParkingLotId(%d)", info.getParkingLotId()));
            });
        } catch (Exception exception) {

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("deleteParkingLotEmployeesByParkingLotId(%s)",
                            notification.getInfoList().stream().map(ParkingLotEmployeeInfo::getParkingLotId).collect(Collectors.toList())));
        }
    }
}

// Node: consumeMessageFromUserTopic
// Node: getTimeInMillis
// Node: toUser
// Node: toUserList
// Node: toCustomer
// Node: getUserInfo
package com.bht.saigonparking.service.user.service.grpc;

import java.util.Arrays;
import java.util.HashSet;
import java.util.List;

import org.apache.logging.log4j.Level;
import org.lognet.springboot.grpc.GRpcService;
import org.springframework.beans.factory.annotation.Autowired;

import com.bht.saigonparking.api.grpc.parkinglot.ParkingLotServiceGrpc;
import com.bht.saigonparking.api.grpc.user.CountAllUserGroupByRoleResponse;
import com.bht.saigonparking.api.grpc.user.CountAllUserRequest;
import com.bht.saigonparking.api.grpc.user.Customer;
import com.bht.saigonparking.api.grpc.user.DeleteMultiUserByIdRequest;
import com.bht.saigonparking.api.grpc.user.GetAllUserRequest;
import com.bht.saigonparking.api.grpc.user.GetAllUserResponse;
import com.bht.saigonparking.api.grpc.user.GetEmployeeManageParkingLotListResponse;
import com.bht.saigonparking.api.grpc.user.MapToUsernameMapRequest;
import com.bht.saigonparking.api.grpc.user.MapToUsernameMapResponse;
import com.bht.saigonparking.api.grpc.user.UpdatePasswordRequest;
import com.bht.saigonparking.api.grpc.user.User;
import com.bht.saigonparking.api.grpc.user.UserRole;
import com.bht.saigonparking.api.grpc.user.UserServiceGrpc.UserServiceImplBase;
import com.bht.saigonparking.common.interceptor.SaigonParkingServerInterceptor;
import com.bht.saigonparking.common.util.LoggingUtil;
import com.bht.saigonparking.service.user.entity.CustomerEntity;
import com.bht.saigonparking.service.user.entity.UserEntity;
import com.bht.saigonparking.service.user.mapper.EnumMapper;
import com.bht.saigonparking.service.user.mapper.UserMapper;
import com.bht.saigonparking.service.user.mapper.UserMapperExt;
import com.bht.saigonparking.service.user.service.main.UserService;
import com.google.protobuf.BoolValue;
import com.google.protobuf.Empty;
import com.google.protobuf.Int64Value;
import com.google.protobuf.StringValue;

import io.grpc.stub.StreamObserver;
import lombok.AllArgsConstructor;

/**
 *
 * this class implements all services of UserStub
 *
 * for clean code purpose,
 * using {@code @AllArgsConstructor} for Service class
 * it will {@code @Autowired} all attributes declared inside
 * hide {@code @Autowired} as much as possible in code
 * remember to mark all attributes as {@code private final}
 *
 * @author bht
 */
@GRpcService
@AllArgsConstructor(onConstructor = @__(@Autowired))
public final class UserServiceGrpcImpl extends UserServiceImplBase {

    private final UserService userService;
    private final UserMapper userMapper;
    private final UserMapperExt userMapperExt;
    private final EnumMapper enumMapper;
    private final SaigonParkingServerInterceptor serverInterceptor;
    private final ParkingLotServiceGrpc.ParkingLotServiceBlockingStub parkingLotServiceBlockingStub;

    @Override
    public void countAllUser(CountAllUserRequest request, StreamObserver<Int64Value> responseObserver) {
        try {
            serverInterceptor.validateAdmin();

            Long count;

            if (request.getUserRole().equals(UserRole.ALL)) {
                count = userService.countAll(request.getKeyword(), request.getInactivatedOnly());

            } else {
                count = userService.countAll(request.getKeyword(), request.getInactivatedOnly(), enumMapper.toUserRoleEntity(request.getUserRole()));
            }

            responseObserver.onNext(Int64Value.of(count));
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success", "countAllUser");

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL", "countAllUser");
        }
    }

    @Override
    public void getAllUser(GetAllUserRequest request, StreamObserver<GetAllUserResponse> responseObserver) {
        try {
            serverInterceptor.validateAdmin();

            List<User> userList;

            if (request.getUserRole().equals(UserRole.ALL)) {
                userList = userMapper.toUserList(userService
                        .getAll(request.getNRow(), request.getPageNumber(), request.getKeyword(), request.getInactivatedOnly()));

            } else {
                userList = userMapper.toUserList(userService
                        .getAll(request.getNRow(), request.getPageNumber(), request.getKeyword(), request.getInactivatedOnly(), enumMapper.toUserRoleEntity(request.getUserRole())));
            }

            responseObserver.onNext(GetAllUserResponse.newBuilder().addAllUser(userList).build());
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("getAllUser(%d, %d)", request.getNRow(), request.getPageNumber()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("getAllUser(%d, %d)", request.getNRow(), request.getPageNumber()));
        }
    }

    @Override
    public void getUserById(Int64Value request, StreamObserver<User> responseObserver) {
        try {
            serverInterceptor.validateAdmin();

            User user = userMapper.toUser(userService
                    .getUserById(request.getValue()));

            responseObserver.onNext(user);
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("getUserById(%d)", request.getValue()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("getUserById(%d)", request.getValue()));
        }
    }

    @Override
    public void getUserByUsername(StringValue request, StreamObserver<User> responseObserver) {
        try {
            User user = userMapper.toUser(userService
                    .getUserByUsername(request.getValue()));

            responseObserver.onNext(user);
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("getUserByUsername(%s)", request.getValue()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("getUserByUsername(%s)", request.getValue()));
        }
    }

    @Override
    public void getCustomerById(Int64Value request, StreamObserver<Customer> responseObserver) {
        try {
            serverInterceptor.validateAdmin();

            Customer customer = userMapper.toCustomer(userService
                    .getCustomerById(request.getValue()));

            responseObserver.onNext(customer);
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("getCustomerById(%d)", request.getValue()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("getCustomerById(%d)", request.getValue()));
        }
    }

    @Override
    public void getCustomerByUsername(StringValue request, StreamObserver<Customer> responseObserver) {
        try {
            CustomerEntity customerEntity = userService.getCustomerByUsername(request.getValue());

            serverInterceptor.validateUser(customerEntity.getId());

            responseObserver.onNext(userMapper.toCustomer(customerEntity));
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("getCustomerByUsername(%s)", request.getValue()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("getCustomerByUsername(%s)", request.getValue()));
        }
    }

    @Override
    public void mapToUsernameMap(MapToUsernameMapRequest request, StreamObserver<MapToUsernameMapResponse> responseObserver) {
        try {
            serverInterceptor.validateAdmin();

            MapToUsernameMapResponse mapToUsernameMapResponse = MapToUsernameMapResponse.newBuilder()
                    .putAllUsername(userService.mapToUsernameMap(new HashSet<>(request.getUserIdList())))
                    .build();

            responseObserver.onNext(mapToUsernameMapResponse);
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success", "mapToUsernameMap()");

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL", "mapToUsernameMap()");
        }
    }

    @Override
    public void mapUserIdToUsername(Int64Value request, StreamObserver<StringValue> responseObserver) {
        try {
            serverInterceptor.validateAdmin();
            String username = userService.getUsernameOfUser(request.getValue());

            responseObserver.onNext(StringValue.of(username));
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("mapUserIdToUsername(%d): %s", request.getValue(), username));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("mapUserIdToUsername(%d)", request.getValue()));
        }
    }

    @Override
    public void createUser(User request, StreamObserver<Int64Value> responseObserver) {
        try {
            serverInterceptor.validateAdmin();

            UserEntity userEntity = userMapperExt.toUserEntity(request, true);
            Long newUserId = userService.createUser(userEntity);

            responseObserver.onNext(Int64Value.of(newUserId));
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("createUser(%s)", request.getUsername()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("createUser(%s)", request.getUsername()));
        }
    }

    @Override
    public void createCustomer(Customer request, StreamObserver<Int64Value> responseObserver) {
        try {
            serverInterceptor.validateAdmin();

            CustomerEntity customerEntity = userMapperExt.toCustomerEntity(request, true);
            Long newCustomerId = userService.createCustomer(customerEntity);

            responseObserver.onNext(Int64Value.of(newCustomerId));
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("createCustomer(%s)", request.getUserInfo().getUsername()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("createCustomer(%s)", request.getUserInfo().getUsername()));
        }
    }

    @Override
    public void updateCustomer(Customer request, StreamObserver<Empty> responseObserver) {
        try {
            CustomerEntity customerEntity = userMapperExt.toCustomerEntity(request, false);

            serverInterceptor.validateUser(customerEntity.getId());

            userService.updateCustomer(customerEntity);

            responseObserver.onNext(Empty.getDefaultInstance());
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("updateCustomer(%s)", request.getUserInfo().getUsername()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("updateCustomer(%s)", request.getUserInfo().getUsername()));
        }
    }

    @Override
    public void updatePassword(UpdatePasswordRequest request, StreamObserver<Empty> responseObserver) {
        try {
            UserEntity userEntity = userService.getUserByUsername(request.getUsername());

            serverInterceptor.validateUser(userEntity.getId());

            userService.updateUserPassword(userEntity, request.getNewPassword());

            responseObserver.onNext(Empty.getDefaultInstance());
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("updatePasswordOfUser(%s)", request.getUsername()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("updatePasswordOfUser(%s)", request.getUsername()));
        }
    }

    @Override
    public void activateUser(Int64Value request, StreamObserver<Empty> responseObserver) {
        try {
            serverInterceptor.validateAdmin();

            userService.activateUserWithId(request.getValue());

            responseObserver.onNext(Empty.getDefaultInstance());
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("activateUserWithId(%d)", request.getValue()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("activateUserWithId(%d)", request.getValue()));
        }
    }

    @Override
    public void deactivateUser(Int64Value request, StreamObserver<Empty> responseObserver) {
        try {
            serverInterceptor.validateAdmin();

            userService.deactivateUserWithId(request.getValue());

            responseObserver.onNext(Empty.getDefaultInstance());
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("deactivateUserWithId(%d)", request.getValue()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("deactivateUserWithId(%d)", request.getValue()));
        }
    }

    @Override
    public void deleteUserById(Int64Value request, StreamObserver<Empty> responseObserver) {
        try {
            serverInterceptor.validateAdmin();

            userService.deleteUserById(request.getValue());

            responseObserver.onNext(Empty.getDefaultInstance());
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("deleteUserById(%d)", request.getValue()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("deleteUserById(%d)", request.getValue()));
        }
    }

    @Override
    public void deleteMultiUserById(DeleteMultiUserByIdRequest request, StreamObserver<Empty> responseObserver) {
        try {
            serverInterceptor.validateAdmin();

            userService.deleteMultiUserById(new HashSet<>(request.getUserIdList()));

            responseObserver.onNext(Empty.getDefaultInstance());
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("deleteMultiUserById(%s)", request.getUserIdList()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("deleteMultiUserById(%s)", request.getUserIdList()));
        }
    }

    @Override
    public void countAllUserGroupByRole(Empty request, StreamObserver<CountAllUserGroupByRoleResponse> responseObserver) {
        try {
            serverInterceptor.validateAdmin();

            CountAllUserGroupByRoleResponse response = CountAllUserGroupByRoleResponse.newBuilder()
                    .putAllRoleCount(userService.countAllUserGroupByRole())
                    .build();

            responseObserver.onNext(response);
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success", "countAllUserGroupByRole()");

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL", "countAllUserGroupByRole()");
        }
    }

    @Override
    public void checkUsernameAlreadyExist(StringValue request, StreamObserver<BoolValue> responseObserver) {
        try {
            serverInterceptor.validateAdmin();

            boolean isUsernameAlreadyExist = userService.checkUsernameAlreadyExist(request.getValue());

            responseObserver.onNext(BoolValue.of(isUsernameAlreadyExist));
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("checkUsernameAlreadyExist(%s): %b", request.getValue(), isUsernameAlreadyExist));

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
            serverInterceptor.validateAdmin();

            boolean isEmailAlreadyExist = userService.checkEmailAlreadyExist(request.getValue());

            responseObserver.onNext(BoolValue.of(isEmailAlreadyExist));
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("checkEmailAlreadyExist(%s): %b", request.getValue(), isEmailAlreadyExist));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("checkEmailAlreadyExist(%s)", request.getValue()));
        }
    }

    @Override
    public void getEmployeeManageParkingLotList(Int64Value request, StreamObserver<GetEmployeeManageParkingLotListResponse> responseObserver) {
        try {
            serverInterceptor.validateUserRole(Arrays.asList("PARKING_LOT_EMPLOYEE", "ADMIN"));

            List<Long> employeeIdList = parkingLotServiceBlockingStub
                    .getEmployeeManageParkingLotIdList(request)
                    .getEmployeeIdList();

            List<User> employeeList = userMapper.toUserList(userService.getAll(new HashSet<>(employeeIdList)));
            GetEmployeeManageParkingLotListResponse response = GetEmployeeManageParkingLotListResponse.newBuilder()
                    .addAllEmployee(employeeList)
                    .build();

            responseObserver.onNext(response);
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("getEmployeeManageParkingLotList(%d)", request.getValue()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("getEmployeeManageParkingLotList(%d)", request.getValue()));
        }
    }
}

// Node: countAllUser
// Node: getInactivatedOnly
// Node: getAllUser
// Node: addAllUser
// Node: putAllUsername
// Node: getUserIdList
// Node: updatePassword
// Node: getNewPassword
// Node: updatePasswordOfUser
// Node: deactivateUser
// Node: putAllRoleCount
// Node: getEmployeeManageParkingLotList
// Node: addAllEmployee
package com.bht.saigonparking.service.booking.configuration;

import static com.bht.saigonparking.api.grpc.booking.BookingStatisticRequestType.CREATE;
import static com.bht.saigonparking.common.constant.SaigonParkingMessageQueue.BOOKING_QUEUE_NAME;

import java.util.HashSet;

import javax.transaction.Transactional;
import javax.validation.constraints.NotNull;

import org.apache.logging.log4j.Level;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.bht.saigonparking.api.grpc.booking.BookingStatisticRequest;
import com.bht.saigonparking.common.util.LoggingUtil;
import com.bht.saigonparking.service.booking.service.main.BookingService;

import lombok.AllArgsConstructor;

/**
 *
 * @author bht
 */
@Service
@Transactional
@AllArgsConstructor(onConstructor = @__(@Autowired))
public class MessageQueueConfiguration {

    private final BookingService bookingService;

    @RabbitListener(queues = {BOOKING_QUEUE_NAME})
    public void consumeMessageFromBookingTopic(@NotNull BookingStatisticRequest request) {
        try {
            switch (request.getType()) {
                case CREATE:
                    bookingService.createOneOrManyParkingLotStatistic(new HashSet<>(request.getParkingLotIdList()));
                    LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                            String.format("createStatisticOfParkingLot: %s", request.getParkingLotIdList()));
                    break;
                case DELETE:
                    bookingService.deleteOneOrManyParkingLotStatistic(new HashSet<>(request.getParkingLotIdList()));
                    LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                            String.format("deleteStatisticOfParkingLot: %s", request.getParkingLotIdList()));
                    break;
                default:
                    break;
            }

        } catch (Exception exception) {

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    (request.getType().equals(CREATE))
                            ? String.format("createStatisticOfParkingLot: %s", request.getParkingLotIdList())
                            : String.format("deleteStatisticOfParkingLot: %s", request.getParkingLotIdList()));
        }
    }
}

// Node: consumeMessageFromBookingTopic
// Node: toBookingList
// Node: toBookingStatusEntity
// Node: toBookingEntityParkingLotNameMap
package com.bht.saigonparking.service.booking.service.grpc;

import java.util.Arrays;
import java.util.List;
import java.util.Map;

import org.apache.logging.log4j.Level;
import org.lognet.springboot.grpc.GRpcService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.util.Pair;

import com.bht.saigonparking.api.grpc.booking.Booking;
import com.bht.saigonparking.api.grpc.booking.BookingDetail;
import com.bht.saigonparking.api.grpc.booking.BookingList;
import com.bht.saigonparking.api.grpc.booking.BookingRating;
import com.bht.saigonparking.api.grpc.booking.BookingServiceGrpc;
import com.bht.saigonparking.api.grpc.booking.BookingStatus;
import com.bht.saigonparking.api.grpc.booking.CountAllBookingGroupByStatusResponse;
import com.bht.saigonparking.api.grpc.booking.CountAllBookingOfParkingLotRequest;
import com.bht.saigonparking.api.grpc.booking.CountAllBookingRequest;
import com.bht.saigonparking.api.grpc.booking.CountAllRatingsOfParkingLotRequest;
import com.bht.saigonparking.api.grpc.booking.CreateBookingRatingRequest;
import com.bht.saigonparking.api.grpc.booking.CreateBookingRequest;
import com.bht.saigonparking.api.grpc.booking.CreateBookingResponse;
import com.bht.saigonparking.api.grpc.booking.DeleteBookingRatingRequest;
import com.bht.saigonparking.api.grpc.booking.FinishBookingRequest;
import com.bht.saigonparking.api.grpc.booking.FinishBookingResponse;
import com.bht.saigonparking.api.grpc.booking.GenerateBookingQrCodeRequest;
import com.bht.saigonparking.api.grpc.booking.GenerateBookingQrCodeResponse;
import com.bht.saigonparking.api.grpc.booking.GetAllBookingOfCustomerRequest;
import com.bht.saigonparking.api.grpc.booking.GetAllBookingOfParkingLotRequest;
import com.bht.saigonparking.api.grpc.booking.GetAllBookingRequest;
import com.bht.saigonparking.api.grpc.booking.GetAllRatingsOfParkingLotRequest;
import com.bht.saigonparking.api.grpc.booking.GetAllRatingsOfParkingLotResponse;
import com.bht.saigonparking.api.grpc.booking.GetBookingRatingRequest;
import com.bht.saigonparking.api.grpc.booking.ParkingLotBookingAndRatingStatistic;
import com.bht.saigonparking.api.grpc.booking.ParkingLotRatingCountGroupByRating;
import com.bht.saigonparking.api.grpc.booking.UpdateBookingRatingRequest;
import com.bht.saigonparking.api.grpc.booking.UpdateBookingStatusRequest;
import com.bht.saigonparking.common.exception.CustomerHasOnGoingBookingException;
import com.bht.saigonparking.common.interceptor.SaigonParkingServerInterceptor;
import com.bht.saigonparking.common.util.ImageUtil;
import com.bht.saigonparking.common.util.LoggingUtil;
import com.bht.saigonparking.service.booking.entity.BookingEntity;
import com.bht.saigonparking.service.booking.mapper.BookingMapper;
import com.bht.saigonparking.service.booking.mapper.CustomizedMapper;
import com.bht.saigonparking.service.booking.mapper.EnumMapper;
import com.bht.saigonparking.service.booking.service.main.BookingService;
import com.bht.saigonparking.service.booking.service.main.QrCodeService;
import com.google.protobuf.BoolValue;
import com.google.protobuf.Empty;
import com.google.protobuf.Int64Value;
import com.google.protobuf.StringValue;

import io.grpc.stub.StreamObserver;
import lombok.RequiredArgsConstructor;

/**
 *
 * @author bht
 */
@GRpcService
@RequiredArgsConstructor(onConstructor = @__(@Autowired))
public final class BookingServiceGrpcImpl extends BookingServiceGrpc.BookingServiceImplBase {

    private final SaigonParkingServerInterceptor serverInterceptor;
    private final EnumMapper enumMapper;
    private final BookingMapper bookingMapper;
    private final CustomizedMapper customizedMapper;
    private final BookingService bookingService;
    private final QrCodeService qrCodeService;

    @Override
    public void createBooking(CreateBookingRequest request, StreamObserver<CreateBookingResponse> responseObserver) {
        try {
            serverInterceptor.validateAdmin();

            if (bookingService.checkCustomerHasOnGoingBooking(request.getCustomerId())) {
                throw new CustomerHasOnGoingBookingException();
            }

            Pair<String, String> newBooking = bookingService.saveNewBooking(bookingMapper.toBookingEntity(request));

            CreateBookingResponse response = CreateBookingResponse.newBuilder()
                    .setBookingId(newBooking.getFirst())
                    .setQrCode(ImageUtil.encodeImage(qrCodeService.encodeContents(newBooking.getFirst())))
                    .setCreatedAt(newBooking.getSecond())
                    .build();

            responseObserver.onNext(response);
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("createBooking(%d, %d, %s)", request.getParkingLotId(), request.getCustomerId(), request.getLicensePlate()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("createBooking(%d, %d, %s)", request.getParkingLotId(), request.getCustomerId(), request.getLicensePlate()));
        }
    }

    @Override
    public void updateBookingStatus(UpdateBookingStatusRequest request, StreamObserver<Empty> responseObserver) {
        try {
            serverInterceptor.validateAdmin();

            bookingService.saveNewBookingHistory(bookingMapper.toBookingHistoryEntity(request), request.getBookingId());

            responseObserver.onNext(Empty.getDefaultInstance());
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("updateBookingStatus(%s): %s", request.getBookingId(), request.getStatus()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("updateBookingStatus(%s): %s", request.getBookingId(), request.getStatus()));
        }
    }

    @Override
    public void deleteBookingById(StringValue request, StreamObserver<Empty> responseObserver) {
        try {
            serverInterceptor.validateAdmin();

            bookingService.deleteBookingByUuid(request.getValue());

            responseObserver.onNext(Empty.getDefaultInstance());
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("deleteBookingById(%s)", request.getValue()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("deleteBookingById(%s)", request.getValue()));
        }
    }

    @Override
    public void countAllBooking(CountAllBookingRequest request, StreamObserver<Int64Value> responseObserver) {
        try {
            serverInterceptor.validateAdmin();

            Long count = request.getStatus().equals(BookingStatus.ALL)
                    ? bookingService.countAllBooking()
                    : bookingService.countAllBooking(enumMapper.toBookingStatusEntity(request.getStatus()));

            responseObserver.onNext(Int64Value.of(count));
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("countAllBooking(%s): %d", request.getStatus(), count));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("countAllBooking(%s)", request.getStatus()));
        }
    }

    @Override
    public void countAllBookingOfCustomerByCustomerId(Int64Value request, StreamObserver<Int64Value> responseObserver) {
        try {
            serverInterceptor.validateAdmin();

            Long count = bookingService.countAllBookingOfCustomer(request.getValue());

            responseObserver.onNext(Int64Value.of(count));
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("countAllBookingOfCustomerByCustomerId(%d): %d", request.getValue(), count));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("countAllBookingOfCustomerByCustomerId(%d)", request.getValue()));
        }
    }

    @Override
    public void countAllBookingOfCustomerByAuthorizationHeader(Empty request, StreamObserver<Int64Value> responseObserver) {
        Long customerId = serverInterceptor.getUserIdContext().get();
        try {
            Long count = bookingService.countAllBookingOfCustomer(customerId);

            responseObserver.onNext(Int64Value.of(count));
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("countAllBookingOfCustomerByAuthorizationHeader(%d): %d", customerId, count));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("countAllBookingOfCustomerByAuthorizationHeader(%d)", customerId));
        }
    }

    @Override
    public void countAllBookingOfParkingLot(CountAllBookingOfParkingLotRequest request, StreamObserver<Int64Value> responseObserver) {
        try {
            Long count = (request.getStatus().equals(BookingStatus.ALL))
                    ? bookingService.countAllBookingOfParkingLot(request.getParkingLotId())
                    : bookingService.countAllBookingOfParkingLot(request.getParkingLotId(), enumMapper.toBookingStatusEntity(request.getStatus()));

            responseObserver.onNext(Int64Value.of(count));
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("countAllBookingOfParkingLot(%d, %s): %d", request.getParkingLotId(), request.getStatus(), count));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("countAllBookingOfParkingLot(%d, %s)", request.getParkingLotId(), request.getStatus()));
        }
    }

    @Override
    public void countAllOnGoingBookingOfParkingLot(Int64Value request, StreamObserver<Int64Value> responseObserver) {
        try {
            Long count = bookingService.countAllOnGoingBookingOfParkingLot(request.getValue());

            responseObserver.onNext(Int64Value.of(count));
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("countAllOnGoingBookingOfParkingLot(%d): %d", request.getValue(), count));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("countAllOnGoingBookingOfParkingLot(%d)", request.getValue()));
        }
    }

    @Override
    public void getAllBooking(GetAllBookingRequest request, StreamObserver<BookingList> responseObserver) {
        try {
            List<BookingEntity> bookingEntityList = request.getStatus().equals(BookingStatus.ALL)
                    ? bookingService.getAllBooking(request.getNRow(), request.getPageNumber())
                    : bookingService.getAllBooking(enumMapper.toBookingStatusEntity(request.getStatus()), request.getNRow(), request.getPageNumber());

            Map<BookingEntity, String> bookingMap = customizedMapper.toBookingEntityParkingLotNameMap(bookingEntityList);
            BookingList bookingList = BookingList.newBuilder().addAllBooking(bookingMapper.toBookingList(bookingMap)).build();

            responseObserver.onNext(bookingList);
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("getAllBooking(%s, %d, %d)", request.getStatus(), request.getNRow(), request.getPageNumber()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("getAllBooking(%s, %d, %d)", request.getStatus(), request.getNRow(), request.getPageNumber()));
        }
    }

    @Override
    public void getAllBookingOfCustomer(GetAllBookingOfCustomerRequest request, StreamObserver<BookingList> responseObserver) {
        Long customerId = serverInterceptor.getRoleContext().get().equals("CUSTOMER")
                ? serverInterceptor.getUserIdContext().get()
                : request.getCustomerId();
        try {
            if (customerId <= 0) {
                throw new IllegalArgumentException();
            }
            List<BookingEntity> bookingEntityList = bookingService
                    .getAllBookingOfCustomer(customerId, request.getNRow(), request.getPageNumber());

            Map<BookingEntity, String> bookingMap = customizedMapper.toBookingEntityParkingLotNameMap(bookingEntityList);
            BookingList bookingList = BookingList.newBuilder().addAllBooking(bookingMapper.toBookingList(bookingMap)).build();

            responseObserver.onNext(bookingList);
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("getAllBookingOfCustomer(%d, %d, %d)", customerId, request.getNRow(), request.getPageNumber()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("getAllBookingOfCustomer(%d, %d, %d)", customerId, request.getNRow(), request.getPageNumber()));
        }
    }

    @Override
    public void getAllBookingOfParkingLot(GetAllBookingOfParkingLotRequest request, StreamObserver<BookingList> responseObserver) {
        try {
            List<BookingEntity> bookingEntityList = request.getStatus().equals(BookingStatus.ALL)
                    ? bookingService.getAllBookingOfParkingLot(request.getParkingLotId(), request.getNRow(), request.getPageNumber())
                    : bookingService.getAllBookingOfParkingLot(request.getParkingLotId(), enumMapper.toBookingStatusEntity(request.getStatus()), request.getNRow(), request.getPageNumber());

            Map<BookingEntity, String> bookingMap = customizedMapper.toBookingEntityParkingLotNameMap(bookingEntityList);
            BookingList bookingList = BookingList.newBuilder().addAllBooking(bookingMapper.toBookingList(bookingMap)).build();

            responseObserver.onNext(bookingList);
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("getAllBookingOfParkingLot(%d, %s, %d, %d)",
                            request.getParkingLotId(), request.getStatus(), request.getNRow(), request.getPageNumber()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("getAllBookingOfParkingLot(%d, %s, %d, %d)",
                            request.getParkingLotId(), request.getStatus(), request.getNRow(), request.getPageNumber()));
        }
    }

    @Override
    public void getAllOnGoingBookingOfParkingLot(Int64Value request, StreamObserver<BookingList> responseObserver) {
        try {
            List<BookingEntity> bookingEntityList = bookingService.getAllOnGoingBookingOfParkingLot(request.getValue());

            Map<BookingEntity, String> bookingMap = customizedMapper.toBookingEntityParkingLotNameMap(bookingEntityList);
            BookingList bookingList = BookingList.newBuilder().addAllBooking(bookingMapper.toBookingList(bookingMap)).build();

            responseObserver.onNext(bookingList);
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("getAllOnGoingBookingOfParkingLot(%d)", request.getValue()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("getAllOnGoingBookingOfParkingLot(%d)", request.getValue()));
        }
    }

    @Override
    public void getBookingDetailByBookingId(StringValue request, StreamObserver<BookingDetail> responseObserver) {
        try {
            BookingEntity bookingEntity = bookingService.getBookingDetailByUuid(request.getValue());

            responseObserver.onNext(bookingMapper.toBookingDetail(bookingEntity));
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("getBookingDetailByBookingId(%s)", request.getValue()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("getBookingDetailByBookingId(%s)", request.getValue()));
        }
    }

    @Override
    public void generateBookingQrCode(GenerateBookingQrCodeRequest request, StreamObserver<GenerateBookingQrCodeResponse> responseObserver) {
        try {
            String bookingUuid = request.getBookingId();

            /* check if booking is exist, otherwise, throw exception */
            bookingService.getBookingByUuid(bookingUuid);

            GenerateBookingQrCodeResponse response = GenerateBookingQrCodeResponse.newBuilder()
                    .setQrCode(ImageUtil.encodeImage(qrCodeService.encodeContents(bookingUuid)))
                    .build();

            responseObserver.onNext(response);
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("generateBookingQrCode(%s)", request.getBookingId()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("generateBookingQrCode(%s)", request.getBookingId()));
        }
    }

    @Override
    public void finishBooking(FinishBookingRequest request, StreamObserver<FinishBookingResponse> responseObserver) {
        try {
            serverInterceptor.validateUserRole(Arrays.asList("PARKING_LOT_EMPLOYEE", "ADMIN"));

            String bookingUuid = request.getBookingId();
            Pair<Long, Long> customerParkingLotPair = bookingService.finishBooking(bookingUuid);

            FinishBookingResponse finishBookingResponse = FinishBookingResponse.newBuilder()
                    .setBookingId(bookingUuid)
                    .setCustomerId(customerParkingLotPair.getFirst())
                    .setParkingLotId(customerParkingLotPair.getSecond())
                    .build();

            responseObserver.onNext(finishBookingResponse);
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("finishBooking(%s)", request.getBookingId()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("finishBooking(%s)", request.getBookingId()));
        }
    }

    @Override
    public void countAllBookingGroupByStatus(Empty request, StreamObserver<CountAllBookingGroupByStatusResponse> responseObserver) {
        try {
            serverInterceptor.validateAdmin();

            CountAllBookingGroupByStatusResponse response = CountAllBookingGroupByStatusResponse.newBuilder()
                    .putAllStatusCount(bookingService.countAllBookingGroupByStatus())
                    .build();

            responseObserver.onNext(response);
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success", "countAllBookingGroupByStatus()");

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL", "countAllBookingGroupByStatus()");
        }
    }

    @Override
    public void countAllBookingOfParkingLotGroupByStatus(Int64Value request, StreamObserver<CountAllBookingGroupByStatusResponse> responseObserver) {
        try {
            serverInterceptor.validateUserRole(Arrays.asList("PARKING_LOT_EMPLOYEE", "ADMIN"));

            CountAllBookingGroupByStatusResponse response = CountAllBookingGroupByStatusResponse.newBuilder()
                    .putAllStatusCount(bookingService.countAllBookingOfParkingLotGroupByStatus(request.getValue()))
                    .build();

            responseObserver.onNext(response);
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("countAllBookingOfParkingLotGroupByStatus(%d)", request.getValue()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("countAllBookingOfParkingLotGroupByStatus(%d)", request.getValue()));
        }
    }

    @Override
    public void checkCustomerHasOnGoingBooking(Empty request, StreamObserver<BoolValue> responseObserver) {
        Long customerId = serverInterceptor.getUserIdContext().get();
        try {
            serverInterceptor.validateUserRole("CUSTOMER");

            boolean isCustomerHasOnGoingBooking = bookingService.checkCustomerHasOnGoingBooking(customerId);

            responseObserver.onNext(BoolValue.of(isCustomerHasOnGoingBooking));
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("checkCustomerHasOnGoingBooking(%d): %b", customerId, isCustomerHasOnGoingBooking));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("checkCustomerHasOnGoingBooking(%d)", customerId));
        }
    }

    @Override
    public void getCustomerOnGoingBooking(Empty request, StreamObserver<Booking> responseObserver) {
        Long customerId = serverInterceptor.getUserIdContext().get();
        try {
            serverInterceptor.validateUserRole("CUSTOMER");
            BookingEntity onGoingBooking = bookingService.getOnGoingBookingOfCustomer(customerId);

            responseObserver.onNext(bookingMapper.toBooking(onGoingBooking));
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("getCustomerOnGoingBooking(%d): %s", customerId, onGoingBooking.getUuid()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("getCustomerOnGoingBooking(%d)", customerId));
        }
    }

    @Override
    public void createBookingRating(CreateBookingRatingRequest request, StreamObserver<Int64Value> responseObserver) {
        Long customerId = serverInterceptor.getUserIdContext().get();
        try {
            serverInterceptor.validateUserRole("CUSTOMER");
            Long newRatingId = bookingService.createBookingRating(customerId, request.getBookingId(), request.getRating(), request.getComment());

            responseObserver.onNext(Int64Value.of(newRatingId));
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("createBookingRating(%s, %d, %s)",
                            request.getBookingId(), request.getRating(), request.getComment()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("createBookingRating(%s, %d, %s)",
                            request.getBookingId(), request.getRating(), request.getComment()));
        }
    }

    @Override
    public void getBookingRating(GetBookingRatingRequest request, StreamObserver<BookingRating> responseObserver) {
        try {
            BookingRating bookingRating = bookingMapper.toBookingRating(bookingService
                    .getBookingRatingWithCustomerUsernameByBookingUuid(request.getBookingId()));

            responseObserver.onNext(bookingRating);
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("getBookingRating(%s)", request.getBookingId()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("getBookingRating(%s)", request.getBookingId()));
        }
    }

    @Override
    public void updateBookingRating(UpdateBookingRatingRequest request, StreamObserver<Empty> responseObserver) {
        Long customerId = serverInterceptor.getUserIdContext().get();
        try {
            serverInterceptor.validateUserRole("CUSTOMER");
            bookingService.updateBookingRating(customerId, request.getBookingId(), request.getRating(), request.getComment());

            responseObserver.onNext(Empty.getDefaultInstance());
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("updateBookingRating(%s, %d, %s)",
                            request.getBookingId(), request.getRating(), request.getComment()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("updateBookingRating(%s, %d, %s)",
                            request.getBookingId(), request.getRating(), request.getComment()));
        }
    }

    @Override
    public void deleteBookingRating(DeleteBookingRatingRequest request, StreamObserver<Empty> responseObserver) {
        Long customerId = serverInterceptor.getUserIdContext().get();
        try {
            serverInterceptor.validateUserRole("CUSTOMER");
            bookingService.deleteBookingRating(customerId, request.getBookingId());

            responseObserver.onNext(Empty.getDefaultInstance());
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("deleteBookingRating(%s)", request.getBookingId()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("deleteBookingRating(%s)", request.getBookingId()));
        }
    }

    @Override
    public void countAllRatingsOfParkingLot(CountAllRatingsOfParkingLotRequest request, StreamObserver<Int64Value> responseObserver) {
        try {
            Long count = bookingService.countAllRatingsOfParkingLot(request.getParkingLotId(), request.getRating());

            responseObserver.onNext(Int64Value.of(count));
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("countAllRatingsOfParkingLot(%d, %d): %d", request.getParkingLotId(), request.getRating(), count));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("countAllRatingsOfParkingLot(%d, %d)", request.getParkingLotId(), request.getRating()));
        }
    }

    @Override
    public void getAllRatingsOfParkingLot(GetAllRatingsOfParkingLotRequest request, StreamObserver<GetAllRatingsOfParkingLotResponse> responseObserver) {
        try {
            List<BookingRating> bookingRatingList = bookingMapper
                    .toBookingRatingList(bookingService
                            .getAllRatingsOfParkingLot(request.getParkingLotId(), request.getRating(),
                                    request.getSortLastUpdatedAsc(), request.getNRow(), request.getPageNumber()));

            GetAllRatingsOfParkingLotResponse getAllRatingsOfParkingLotResponse = GetAllRatingsOfParkingLotResponse.newBuilder()
                    .addAllRating(bookingRatingList)
                    .build();

            responseObserver.onNext(getAllRatingsOfParkingLotResponse);
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("getAllRatingsOfParkingLot(%d, %d, %b, %d, %d)", request.getParkingLotId(), request.getRating(),
                            request.getSortLastUpdatedAsc(), request.getNRow(), request.getPageNumber()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("getAllRatingsOfParkingLot(%d, %d, %b, %d, %d)", request.getParkingLotId(), request.getRating(),
                            request.getSortLastUpdatedAsc(), request.getNRow(), request.getPageNumber()));
        }
    }

    @Override
    public void getParkingLotRatingCountGroupByRating(Int64Value request, StreamObserver<ParkingLotRatingCountGroupByRating> responseObserver) {
        try {
            ParkingLotRatingCountGroupByRating ratingCountGroupByRating = ParkingLotRatingCountGroupByRating.newBuilder()
                    .putAllRatingCount(bookingService.getParkingLotRatingCountGroupByRating(request.getValue()))
                    .build();

            responseObserver.onNext(ratingCountGroupByRating);
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("getParkingLotRatingCountGroupByRating(%d)", request.getValue()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("getParkingLotRatingCountGroupByRating(%d)", request.getValue()));
        }
    }

    @Override
    public void getParkingLotBookingAndRatingStatistic(Int64Value request, StreamObserver<ParkingLotBookingAndRatingStatistic> responseObserver) {
        try {
            ParkingLotBookingAndRatingStatistic statistic = bookingMapper
                    .toParkingLotBookingAndRatingStatistic(bookingService
                            .getParkingLotBookingAndRatingStatistic(request.getValue()));

            responseObserver.onNext(statistic);
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("getParkingLotBookingAndRatingStatistic(%d)", request.getValue()));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("getParkingLotBookingAndRatingStatistic(%d)", request.getValue()));
        }
    }
}

// Node: updateBookingStatus
// Node: getBookingId
// Node: getStatus
// Node: deleteBookingById
// Node: countAllBookingOfCustomerByCustomerId
// Node: countAllBookingOfCustomerByAuthorizationHeader
// Node: addAllBooking
// Node: getRoleContext
// Node: IllegalArgumentException
// Node: getBookingDetailByBookingId
// Node: generateBookingQrCode
// Node: putAllStatusCount
// Node: getCustomerOnGoingBooking
// Node: getRating
// Node: getComment
// Node: getBookingRating
// Node: getSortLastUpdatedAsc
// Node: addAllRating
// Node: putAllRatingCount
package com.bht.saigonparking.service.contact.service.grpc;

import org.apache.logging.log4j.Level;
import org.lognet.springboot.grpc.GRpcService;
import org.springframework.beans.factory.annotation.Autowired;

import com.bht.saigonparking.api.grpc.contact.ContactServiceGrpc;
import com.bht.saigonparking.api.grpc.contact.GenerateSocketConnectQrCodeRequest;
import com.bht.saigonparking.api.grpc.contact.GenerateSocketConnectQrCodeResponse;
import com.bht.saigonparking.common.interceptor.SaigonParkingServerInterceptor;
import com.bht.saigonparking.common.util.ImageUtil;
import com.bht.saigonparking.common.util.LoggingUtil;
import com.bht.saigonparking.service.contact.service.ConnectivityService;
import com.bht.saigonparking.service.contact.service.QrCodeService;
import com.google.protobuf.BoolValue;
import com.google.protobuf.Int64Value;

import io.grpc.stub.StreamObserver;
import lombok.RequiredArgsConstructor;

/**
 *
 * @author bht
 */
@GRpcService
@RequiredArgsConstructor(onConstructor = @__(@Autowired))
public final class ContactServiceGrpcImpl extends ContactServiceGrpc.ContactServiceImplBase {

    private final QrCodeService qrCodeService;
    private final ConnectivityService connectivityService;
    private final SaigonParkingServerInterceptor serverInterceptor;

    @Override
    public void checkUserOnlineByUserId(Int64Value request, StreamObserver<BoolValue> responseObserver) {
        try {
            boolean isOnline = connectivityService.isUserOnline(request.getValue());

            responseObserver.onNext(BoolValue.of(isOnline));
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("checkUserOnlineByUserId(%d): %b", request.getValue(), isOnline));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("checkUserOnlineByUserId(%d)", request.getValue()));
        }
    }

    @Override
    public void checkParkingLotOnlineByParkingLotId(Int64Value request, StreamObserver<BoolValue> responseObserver) {
        try {
            boolean isOnline = connectivityService.isParkingLotOnline(request.getValue());

            responseObserver.onNext(BoolValue.of(isOnline));
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("checkParkingLotOnlineByParkingLotId(%d): %b", request.getValue(), isOnline));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("checkParkingLotOnlineByParkingLotId(%d)", request.getValue()));
        }
    }

    @Override
    public void generateSocketConnectQrCode(GenerateSocketConnectQrCodeRequest request, StreamObserver<GenerateSocketConnectQrCodeResponse> responseObserver) {
        long userId = serverInterceptor.getUserIdContext().get();
        try {
            GenerateSocketConnectQrCodeResponse response = GenerateSocketConnectQrCodeResponse.newBuilder()
                    .setQrCode(ImageUtil.encodeImage(qrCodeService.encodeContents(request.getAccessToken())))
                    .build();

            responseObserver.onNext(response);
            responseObserver.onCompleted();

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("generateSocketConnectQrCodeForUser(%d)", userId));

        } catch (Exception exception) {

            responseObserver.onError(exception);

            LoggingUtil.log(Level.ERROR, "SERVICE", "Exception", exception.getClass().getSimpleName());
            LoggingUtil.log(Level.WARN, "SERVICE", "Session FAIL",
                    String.format("generateSocketConnectQrCodeForUser(%d)", userId));
        }
    }
}

// Node: generateSocketConnectQrCode
// Node: getAccessToken
// Node: generateSocketConnectQrCodeForUser
package com.bht.saigonparking.service.contact.service.impl;

import static com.bht.saigonparking.api.grpc.contact.SaigonParkingMessage.Classification.PARKING_LOT_MESSAGE;
import static com.bht.saigonparking.api.grpc.contact.SaigonParkingMessage.Classification.SYSTEM_MESSAGE;
import static com.bht.saigonparking.api.grpc.contact.SaigonParkingMessage.Type.BOOKING_PROCESSING;

import java.io.IOException;
import java.sql.Timestamp;

import javax.validation.constraints.NotNull;

import org.apache.logging.log4j.Level;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.web.socket.BinaryMessage;
import org.springframework.web.socket.WebSocketSession;

import com.bht.saigonparking.api.grpc.booking.BookingServiceGrpc;
import com.bht.saigonparking.api.grpc.booking.BookingStatus;
import com.bht.saigonparking.api.grpc.booking.CreateBookingRequest;
import com.bht.saigonparking.api.grpc.booking.CreateBookingResponse;
import com.bht.saigonparking.api.grpc.booking.UpdateBookingStatusRequest;
import com.bht.saigonparking.api.grpc.contact.BookingAcceptanceContent;
import com.bht.saigonparking.api.grpc.contact.BookingCancellationContent;
import com.bht.saigonparking.api.grpc.contact.BookingProcessingContent;
import com.bht.saigonparking.api.grpc.contact.BookingRejectContent;
import com.bht.saigonparking.api.grpc.contact.BookingRequestContent;
import com.bht.saigonparking.api.grpc.contact.SaigonParkingMessage;
import com.bht.saigonparking.common.util.LoggingUtil;
import com.bht.saigonparking.service.contact.service.IntermediateService;
import com.bht.saigonparking.service.contact.service.MessagingService;
import com.google.protobuf.Empty;
import com.google.protobuf.InvalidProtocolBufferException;

import io.grpc.Context;
import io.grpc.stub.StreamObserver;
import lombok.RequiredArgsConstructor;

/**
 *
 * @author bht
 */
@Service
@RequiredArgsConstructor(onConstructor = @__({@Autowired}))
public final class IntermediateServiceImpl implements IntermediateService {

    private final BookingServiceGrpc.BookingServiceStub bookingServiceStub;
    private final BookingServiceGrpc.BookingServiceBlockingStub bookingServiceBlockingStub;

    @Override
    public void handleBookingRequest(@NotNull SaigonParkingMessage.Builder message,
                                     @NotNull WebSocketSession webSocketSession) throws IOException {

        BookingRequestContent.Builder bookingRequestContentBuilder = BookingRequestContent.newBuilder()
                .mergeFrom(message.getContent());

        CreateBookingResponse newBooking = bookingServiceBlockingStub.createBooking(CreateBookingRequest.newBuilder()
                .setParkingLotId(bookingRequestContentBuilder.getParkingLotId())
                .setCustomerId(message.getSenderId())
                .setLicensePlate(bookingRequestContentBuilder.getCustomerLicense())
                .build());

        BookingProcessingContent bookingProcessingContent = BookingProcessingContent.newBuilder()
                .setParkingLotId(bookingRequestContentBuilder.getParkingLotId())
                .setBookingId(newBooking.getBookingId())
                .setCreatedAt(newBooking.getCreatedAt())
                .setQrCode(newBooking.getQrCode())
                .build();

        SaigonParkingMessage bookingProcessingMessage = SaigonParkingMessage.newBuilder()
                .setSenderId(0)
                .setReceiverId(message.getSenderId())
                .setClassification(SYSTEM_MESSAGE)
                .setType(BOOKING_PROCESSING)
                .setContent(bookingProcessingContent.toByteString())
                .build();

        /* attach new booking Id to forward to parking-lot */
        message.setContent(bookingRequestContentBuilder.setBookingId(newBooking.getBookingId()).build().toByteString());

        /* notify new booking Id to customer */
        webSocketSession.sendMessage(new BinaryMessage(bookingProcessingMessage.toByteArray()));
    }

    @Override
    @SuppressWarnings("all")
    public void handleBookingCancellation(@NotNull SaigonParkingMessage.Builder message,
                                          @NotNull MessagingService messagingService) throws InvalidProtocolBufferException {

        BookingCancellationContent bookingCancellationContent = BookingCancellationContent.parseFrom(message.getContent());

        UpdateBookingStatusRequest request = UpdateBookingStatusRequest.newBuilder()
                .setBookingId(bookingCancellationContent.getBookingId())
                .setStatus(BookingStatus.CANCELLED)
                .setNote(bookingCancellationContent.getReason())
                .build();

        bookingServiceBlockingStub.updateBookingStatus(request);
    }

    @Override
    public void handleBookingAcceptance(@NotNull SaigonParkingMessage.Builder message,
                                        @NotNull MessagingService messagingService) throws InvalidProtocolBufferException {

        BookingAcceptanceContent bookingAcceptanceContent = BookingAcceptanceContent.parseFrom(message.getContent());

        UpdateBookingStatusRequest request = UpdateBookingStatusRequest.newBuilder()
                .setBookingId(bookingAcceptanceContent.getBookingId())
                .setStatus(BookingStatus.ACCEPTED)
                .build();

        updateBookingStatus(request, message, messagingService);
    }

    @Override
    public void handleBookingReject(@NotNull SaigonParkingMessage.Builder message,
                                    @NotNull MessagingService messagingService) throws InvalidProtocolBufferException {

        BookingRejectContent bookingRejectContent = BookingRejectContent.parseFrom(message.getContent());

        UpdateBookingStatusRequest request = UpdateBookingStatusRequest.newBuilder()
                .setBookingId(bookingRejectContent.getBookingId())
                .setStatus(BookingStatus.REJECTED)
                .setNote(bookingRejectContent.getReason())
                .build();

        updateBookingStatus(request, message, messagingService);
    }

    private void updateBookingStatus(@NotNull UpdateBookingStatusRequest request,
                                     @NotNull SaigonParkingMessage.Builder message,
                                     @NotNull MessagingService messagingService) {

        Context.current().run(() -> bookingServiceStub
                .updateBookingStatus(request, updateBookingStatusStreamObserver(request, message, messagingService)));
    }

    private StreamObserver<Empty> updateBookingStatusStreamObserver(@NotNull UpdateBookingStatusRequest request,
                                                                    @NotNull SaigonParkingMessage.Builder message,
                                                                    @NotNull MessagingService messagingService) {
        return new StreamObserver<Empty>() {
            @Override
            public void onNext(Empty empty) {
                if (message.getClassification().equals(PARKING_LOT_MESSAGE)) {
                    messagingService.forwardMessageToParkingLot(SaigonParkingMessage.newBuilder()
                            .setClassification(SYSTEM_MESSAGE)
                            .setType(message.getType())
                            .setSenderId(0)
                            .setReceiverId(message.getSenderId())
                            .setContent(message.getContent())
                            .setTimestamp(new Timestamp(System.currentTimeMillis()).toString())
                            .build());
                }
            }

            @Override
            public void onError(Throwable throwable) {
                LoggingUtil.log(Level.ERROR,
                        String.format("updateBookingStatus(%s, %s)", request.getBookingId(), request.getStatus()),
                        "Exception", throwable.getClass().getSimpleName());
            }

            @Override
            public void onCompleted() {
                LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                        String.format("updateBookingStatus(%s, %s)", request.getBookingId(), request.getStatus()));
            }
        };
    }
}

package com.bht.saigonparking.service.contact.service.impl;

import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;

import org.apache.logging.log4j.Level;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.web.socket.BinaryMessage;
import org.springframework.web.socket.WebSocketSession;

import com.bht.saigonparking.api.grpc.booking.BookingServiceGrpc.BookingServiceStub;
import com.bht.saigonparking.api.grpc.booking.FinishBookingRequest;
import com.bht.saigonparking.api.grpc.booking.FinishBookingResponse;
import com.bht.saigonparking.api.grpc.contact.AvailabilityUpdateContent;
import com.bht.saigonparking.api.grpc.contact.BookingFinishContent;
import com.bht.saigonparking.api.grpc.contact.SaigonParkingMessage;
import com.bht.saigonparking.api.grpc.parkinglot.ParkingLotServiceGrpc.ParkingLotServiceStub;
import com.bht.saigonparking.api.grpc.parkinglot.UpdateParkingLotAvailabilityRequest;
import com.bht.saigonparking.common.util.LoggingUtil;
import com.bht.saigonparking.service.contact.handler.WebSocketUserSessionManagement;
import com.bht.saigonparking.service.contact.service.ContactService;
import com.bht.saigonparking.service.contact.service.MessagingService;
import com.google.protobuf.Empty;
import com.google.protobuf.InvalidProtocolBufferException;

import io.grpc.Context;
import io.grpc.stub.StreamObserver;
import lombok.AllArgsConstructor;
import lombok.SneakyThrows;

/**
 *
 * @author bht
 */
@Service
@AllArgsConstructor(onConstructor = @__(@Autowired))
public final class ContactServiceImpl implements ContactService {

    private final MessagingService messagingService;
    private final BookingServiceStub bookingServiceStub;
    private final ParkingLotServiceStub parkingLotServiceStub;
    private final WebSocketUserSessionManagement webSocketUserSessionManagement;

    @Override
    public void handleMessageSendToSystem(@NotNull SaigonParkingMessage message,
                                          @NotNull WebSocketSession session) throws InvalidProtocolBufferException {

        switch (message.getType()) {
            case AVAILABILITY_UPDATE:
                updateAvailability(message, session);
                break;
            case BOOKING_FINISH:
                finishBooking(message, session);
                break;
            default:
                break;
        }
    }

    private void updateAvailability(@NotNull SaigonParkingMessage message,
                                    @NotNull WebSocketSession session) throws InvalidProtocolBufferException {

        AvailabilityUpdateContent content = AvailabilityUpdateContent.parseFrom(message.getContent());

        String userRole = webSocketUserSessionManagement.getUserRoleFromSession(session);

        if ("PARKING_LOT_EMPLOYEE".equals(userRole)) {

            UpdateParkingLotAvailabilityRequest request = UpdateParkingLotAvailabilityRequest.newBuilder()
                    .setParkingLotId(content.getParkingLotId())
                    .setNewAvailability(content.getNewAvailability())
                    .build();

            /* Asynchronously update parking-lot availability */
            Context context = Context.current().fork();
            context.run(() -> parkingLotServiceStub.updateParkingLotAvailability(request, new StreamObserver<Empty>() {
                @Override
                public void onNext(Empty empty) {
                    // ...
                }

                @Override
                public void onError(Throwable throwable) {
                    LoggingUtil.log(Level.ERROR,
                            String.format("updateParkingLotAvailability(%d, %d)", request.getParkingLotId(), request.getNewAvailability()),
                            "Exception", throwable.getClass().getSimpleName());
                }

                @Override
                public void onCompleted() {
                    LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                            String.format("updateParkingLotAvailability(%d, %d)", request.getParkingLotId(), request.getNewAvailability()));
                }
            }));
        }
    }

    @SuppressWarnings("unused")
    private void finishBooking(@NotNull SaigonParkingMessage message,
                               @NotNull WebSocketSession session) throws InvalidProtocolBufferException {

        BookingFinishContent bookingFinishContent = BookingFinishContent.parseFrom(message.getContent());
        String userRole = webSocketUserSessionManagement.getUserRoleFromSession(session);

        if ("PARKING_LOT_EMPLOYEE".equals(userRole)) {
            FinishBookingRequest request = FinishBookingRequest.newBuilder()
                    .setBookingId(bookingFinishContent.getBookingId())
                    .build();

            /* Asynchronously update booking status to FINISHED */
            Context context = Context.current().fork();
            context.run(() -> bookingServiceStub.finishBooking(request, new StreamObserver<FinishBookingResponse>() {
                @Override
                public void onNext(FinishBookingResponse response) {
                    notifyBookingFinish(session, response.getBookingId(), response.getCustomerId(), response.getParkingLotId());
                }

                @Override
                public void onError(Throwable throwable) {
                    LoggingUtil.log(Level.ERROR,
                            String.format("updateBookingStatus(%s, FINISHED)", request.getBookingId()),
                            "Exception", throwable.getClass().getSimpleName());
                }

                @Override
                public void onCompleted() {
                    LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                            String.format("updateBookingStatus(%s, FINISHED)", request.getBookingId()));
                }
            }));
        }
    }

    @SneakyThrows
    private void notifyBookingFinish(@NotNull WebSocketSession session,
                                     @NotEmpty String bookingUuid,
                                     @NotNull Long customerId,
                                     @NotNull Long parkingLotId) {

        SaigonParkingMessage.Builder saigonParkingMessageBuilder = SaigonParkingMessage.newBuilder()
                .setClassification(SaigonParkingMessage.Classification.SYSTEM_MESSAGE)
                .setType(SaigonParkingMessage.Type.BOOKING_FINISH)
                .setSenderId(0)
                .setContent(BookingFinishContent.newBuilder().setBookingId(bookingUuid).build().toByteString());

        /* notify customer that booking has been finished */
        SaigonParkingMessage toCustomerMessage = saigonParkingMessageBuilder.setReceiverId(customerId).build();
        messagingService.forwardMessageToCustomer(toCustomerMessage);

        /* notify parking-lot (another concurrent account) that booking has been finished */
        SaigonParkingMessage toParkingLotMessage = saigonParkingMessageBuilder.setReceiverId(parkingLotId).build();
        messagingService.forwardMessageToParkingLot(toParkingLotMessage);

        /* if current session is auxiliary, then notify to current session that task has been done successfully */
        if (webSocketUserSessionManagement.getUserAuxiliaryFromSession(session)) {
            session.sendMessage(new BinaryMessage(toParkingLotMessage.toByteArray()));
        }
    }
}

package com.bht.saigonparking.service.contact.service.impl;

import java.io.IOException;
import java.util.Set;

import javax.validation.constraints.NotNull;

import org.apache.logging.log4j.Level;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.web.socket.BinaryMessage;
import org.springframework.web.socket.WebSocketSession;

import com.bht.saigonparking.api.grpc.contact.SaigonParkingMessage;
import com.bht.saigonparking.common.constant.SaigonParkingMessageQueue;
import com.bht.saigonparking.common.util.LoggingUtil;
import com.bht.saigonparking.service.contact.handler.WebSocketUserSessionManagement;
import com.bht.saigonparking.service.contact.service.IntermediateService;
import com.bht.saigonparking.service.contact.service.MessagingService;

import lombok.NonNull;
import lombok.RequiredArgsConstructor;

/**
 *
 * @author bht
 */
@Service
@RequiredArgsConstructor(onConstructor = @__({@Autowired}))
public class MessagingServiceImpl implements MessagingService {

    private final RabbitTemplate rabbitTemplate;
    private final IntermediateService intermediateService;
    private final WebSocketUserSessionManagement webSocketUserSessionManagement;

    @Override
    public void prePublishMessageToQueue(@NotNull SaigonParkingMessage.Builder delegate,
                                         @NotNull WebSocketSession webSocketSession) throws IOException {

        switch (delegate.getClassification()) {
            case CUSTOMER_MESSAGE:
                delegate.setSenderId(webSocketUserSessionManagement.getUserIdFromSession(webSocketSession));
                break;
            case PARKING_LOT_MESSAGE:
                delegate.setSenderId(webSocketUserSessionManagement.getParkingLotIdFromSession(webSocketSession));
                break;
            default:
                break;
        }
        preProcessingMessage(delegate, webSocketSession);
    }

    @Override
    public void publishMessageToQueue(@NotNull SaigonParkingMessage saigonParkingMessage) {
        switch (saigonParkingMessage.getClassification()) {
            case PARKING_LOT_MESSAGE:
                forwardMessageToCustomer(saigonParkingMessage);
                return;
            case CUSTOMER_MESSAGE:
                forwardMessageToParkingLot(saigonParkingMessage);
                return;
            default:
                break;
        }
    }

    @Async
    @Override
    public void consumeMessageFromQueue(@NotNull SaigonParkingMessage saigonParkingMessage, @NotNull Long receiverUserId) {
        Set<WebSocketSession> userSessionSet = webSocketUserSessionManagement.getAllSessionOfUser(receiverUserId);
        if (userSessionSet != null) {
            userSessionSet.stream().filter(this::isSessionConsumeMessageFromQueue).forEach(userSession -> {
                try {
                    userSession.sendMessage(new BinaryMessage(saigonParkingMessage.toByteArray()));

                } catch (IOException e) {
                    LoggingUtil.log(Level.ERROR, String.format("forwardMessageToReceiver(%d)", receiverUserId),
                            "Exception", e.getMessage());
                }
            });
        }
        LoggingUtil.log(Level.INFO, "SERVICE", String.format("forwardMessageToReceiver(%d)", receiverUserId),
                String.format("nSessionOfReceiver: %d", (userSessionSet != null) ? userSessionSet.size() : 0));
    }

    @Async
    @Override
    public void forwardMessageToCustomer(@NotNull SaigonParkingMessage message) {
        try {
            String routingKey = SaigonParkingMessageQueue.getUserRoutingKey(message.getReceiverId());
            rabbitTemplate.convertAndSend(routingKey, message);

        } catch (Exception exception) {
            LoggingUtil.log(Level.ERROR, "forwardMessageToCustomer", "Exception", exception.getClass().getSimpleName());
        }
    }

    @Async
    @Override
    public void forwardMessageToParkingLot(@NotNull SaigonParkingMessage message) {
        try {
            String exchangeName = SaigonParkingMessageQueue.getParkingLotExchangeName(message.getReceiverId());
            rabbitTemplate.convertAndSend(exchangeName, "", message);

        } catch (Exception exception) {
            LoggingUtil.log(Level.ERROR, "forwardMessageToParkingLot", "Exception", exception.getClass().getSimpleName());
        }
    }

    private void preProcessingMessage(@NotNull SaigonParkingMessage.Builder delegate,
                                      @NotNull WebSocketSession webSocketSession) throws IOException {
        switch (delegate.getType()) {
            case BOOKING_REQUEST:
                intermediateService.handleBookingRequest(delegate, webSocketSession);
                break;
            case BOOKING_CANCELLATION:
                intermediateService.handleBookingCancellation(delegate, this);
                break;
            case BOOKING_ACCEPTANCE:
                intermediateService.handleBookingAcceptance(delegate, this);
                break;
            case BOOKING_REJECT:
                intermediateService.handleBookingReject(delegate, this);
                break;
            default:
                break;
        }
    }

    private boolean isSessionConsumeMessageFromQueue(@NonNull WebSocketSession session) {
        return !webSocketUserSessionManagement.getUserAuxiliaryFromSession(session);
    }
}

package com.bht.saigonparking.service.contact.handler;

import java.io.IOException;

import org.apache.logging.log4j.Level;
import org.springframework.lang.NonNull;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import com.bht.saigonparking.common.util.LoggingUtil;

import lombok.RequiredArgsConstructor;

/**
 *
 * @author bht
 */
@Component
@RequiredArgsConstructor
public final class WebSocketTextMessageHandler extends TextWebSocketHandler {

    private static final String LOGGING_KEY = "WebSocketTextMessageHandler";
    private final WebSocketUserSessionManagement webSocketUserSessionManagement;

    @Override
    public void afterConnectionEstablished(@NonNull WebSocketSession session) throws IOException {
        Long userId = webSocketUserSessionManagement.getUserIdFromSession(session);
        webSocketUserSessionManagement.addNewUserSession(userId, session);
        LoggingUtil.log(Level.INFO, LOGGING_KEY, "connectionEstablishedWithUser", userId.toString());
        session.sendMessage(new TextMessage("{ \"notification\":\"Connection to Contact service established !\" }"));
    }

    @Override
    public void afterConnectionClosed(@NonNull WebSocketSession session, @NonNull CloseStatus status) {
        Long userId = webSocketUserSessionManagement.getUserIdFromSession(session);
        LoggingUtil.log(Level.INFO, LOGGING_KEY, "connectionClosedFromUser", userId.toString());
        webSocketUserSessionManagement.removeUserSession(userId, session);
    }

    @Override
    public void handleTransportError(@NonNull WebSocketSession session, @NonNull Throwable exception) {
        Long userId = webSocketUserSessionManagement.getUserIdFromSession(session);
        LoggingUtil.log(Level.INFO, LOGGING_KEY, "transportErrorFromSessionOfUser", userId.toString());
        LoggingUtil.log(Level.INFO, LOGGING_KEY, "transportErrorException", exception.getClass().getSimpleName());
    }

    @Override
    protected void handleTextMessage(@NonNull WebSocketSession session, @NonNull TextMessage message) {
        Long userId = webSocketUserSessionManagement.getUserIdFromSession(session);
        LoggingUtil.log(Level.INFO, LOGGING_KEY, "handleTextMessage", String.format("newTextMessageFromUser(%d)", userId));
    }
}

package com.bht.saigonparking.emulator.interceptor;

import org.springframework.stereotype.Component;

import io.grpc.CallOptions;
import io.grpc.Channel;
import io.grpc.ClientCall;
import io.grpc.ClientInterceptor;
import io.grpc.ForwardingClientCall;
import io.grpc.Metadata;
import io.grpc.Metadata.Key;
import io.grpc.MethodDescriptor;

/**
 *
 * @author bht
 */
@Component
public final class AuthTokenProvideInterceptor implements ClientInterceptor {

    private static final String INTERNAL_KEY_NAME = "saigon-parking-internal";
    private static final Key<String> INTERNAL_SERVICE_KEY = Key.of(INTERNAL_KEY_NAME, Metadata.ASCII_STRING_MARSHALLER);

    @Override
    public <ReqT, RespT> ClientCall<ReqT, RespT> interceptCall(MethodDescriptor<ReqT, RespT> methodDescriptor, CallOptions callOptions, Channel channel) {
        return new ForwardingClientCall.SimpleForwardingClientCall<ReqT, RespT>(channel.newCall(methodDescriptor, callOptions)) {
            @Override
            public void start(Listener<RespT> responseListener, Metadata headers) {
                headers.put(INTERNAL_SERVICE_KEY, "165305061220760000");
                super.start(responseListener, headers);
            }
        };
    }
}

// Node: repos/cloned_ms_repos/saigonparking/emulator/src/main/java/com/bht/saigonparking/emulator/interceptor/AuthTokenProvideInterceptor.java:AuthTokenProvideInterceptor.<init>
package com.bht.saigonparking.emulator.util;

import org.apache.logging.log4j.Level;

import lombok.extern.log4j.Log4j2;

/**
 *
 * @author bht
 */
@Log4j2
public final class LoggingUtil {

    private LoggingUtil() {
    }

    public static void log(Level logLevel, String key, String description, String value) {
        log.log(logLevel, format(key, description, value));
    }

    private static String format(String key, String description, String value) {
        return String.format("%-10s %-14s %s",
                "[" + key + "]",
                description + ":",
                value);
    }
}

