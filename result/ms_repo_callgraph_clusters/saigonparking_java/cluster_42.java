// Cluster 42

// Node: build
package com.bht.saigonparking.common.constant;

import java.util.regex.Matcher;
import java.util.regex.Pattern;

import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;

import com.bht.saigonparking.common.exception.IncorrectQueueNameException;

import lombok.AccessLevel;
import lombok.NoArgsConstructor;

/**
 *
 * @author bht
 */
@NoArgsConstructor(access = AccessLevel.NONE)
public final class SaigonParkingMessageQueue {

    public static final String CONTACT_EXCHANGE_NAME = "saigonparking-contact.exchange";
    public static final String INTERNAL_EXCHANGE_NAME = "saigonparking-internal.exchange";

    public static final String BOOKING_QUEUE_NAME = "saigonparking.booking";
    public static final String MAIL_QUEUE_NAME = "saigonparking.mail";
    public static final String USER_QUEUE_NAME = "saigonparking.user";
    public static final String PARKING_LOT_QUEUE_NAME = "saigonparking.parkinglot";

    public static final String BOOKING_TOPIC_ROUTING_KEY = "saigonparking.booking";
    public static final String MAIL_TOPIC_ROUTING_KEY = "saigonparking.mail";
    public static final String USER_TOPIC_ROUTING_KEY = "saigonparking.user";
    public static final String PARKING_LOT_TOPIC_ROUTING_KEY = "saigonparking.parkinglot";

    private static final Pattern USER_QUEUE_NAME_PATTERN = Pattern.compile("user_(\\d+)_queue");

    public static String generateUserRoutingKey(@NotNull Long userId) {
        return getUserQueueName(userId) + ".#";
    }

    public static String getUserRoutingKey(@NotNull Long userId) {
        return getUserQueueName(userId);
    }

    public static String getUserQueueName(@NotNull Long userId) {
        return String.format("user_%d_queue", userId);
    }

    public static String getParkingLotExchangeName(@NotNull Long parkingLotId) {
        return String.format("parking_lot_%d_exchange", parkingLotId);
    }

    public static Long getUserIdFromUserQueueName(@NotEmpty String userQueueName) {
        Matcher matcher = USER_QUEUE_NAME_PATTERN.matcher(userQueueName);
        if (matcher.find()) {
            String userId = matcher.group(1);
            return Long.valueOf(userId);
        }
        throw new IncorrectQueueNameException();
    }
}

// Node: repos/cloned_ms_repos/saigonparking/common/src/main/java/com/bht/saigonparking/common/constant/SaigonParkingMessageQueue.java:SaigonParkingMessageQueue.<init>
// Node: NoArgsConstructor
// Node: compile
// Node: user_
package com.bht.saigonparking.common.auth;

import java.util.Date;

import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.ToString;

/**
 *
 * @author bht
 */
@Getter
@Builder
@ToString
@NoArgsConstructor(access = AccessLevel.NONE)
@AllArgsConstructor(access = AccessLevel.PACKAGE)
public final class SaigonParkingTokenBody {

    private final String tokenId;
    private final SaigonParkingTokenType tokenType;
    private final Long userId;
    private final String userRole;
    private final Date exp;
}

// Node: repos/cloned_ms_repos/saigonparking/common/src/main/java/com/bht/saigonparking/common/auth/SaigonParkingTokenBody.java:SaigonParkingTokenBody.<init>
// Node: AllArgsConstructor
package com.bht.saigonparking.service.auth.configuration;

import java.util.concurrent.TimeUnit;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.client.discovery.DiscoveryClient;
import org.springframework.context.annotation.Bean;
import org.springframework.stereotype.Component;

import com.bht.saigonparking.api.grpc.user.UserServiceGrpc;
import com.bht.saigonparking.common.interceptor.SaigonParkingClientInterceptor;
import com.bht.saigonparking.common.loadbalance.SaigonParkingNameResolverProvider;

import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import lombok.AllArgsConstructor;

/**
 *
 * @author bht
 */
@Component
@AllArgsConstructor(onConstructor = @__(@Autowired))
public final class ChannelConfiguration {

    private final SaigonParkingClientInterceptor clientInterceptor;

    @Bean("userResolver")
    public SaigonParkingNameResolverProvider userServiceNameResolverProvider(@Value("${connection.user-service.id}") String serviceId,
                                                                             @Autowired DiscoveryClient discoveryClient) {
        return new SaigonParkingNameResolverProvider(serviceId, discoveryClient);
    }


    /**
     *
     * channel is the abstraction to connect to a service endpoint
     *
     * note for gRPC service stub:
     *      .newStub(channel)          --> nonblocking/asynchronous stub
     *      .newBlockingStub(channel)  --> blocking/synchronous stub
     */
    @Bean("userChannel")
    public ManagedChannel managedChannel(@Value("${spring.cloud.consul.host}") String host,
                                         @Value("${spring.cloud.consul.port}") int port,
                                         @Value("${connection.idle-timeout}") int timeout,
                                         @Value("${connection.max-inbound-message-size}") int maxInBoundMessageSize,
                                         @Value("${connection.max-inbound-metadata-size}") int maxInBoundMetadataSize,
                                         @Value("${connection.load-balancing-policy}") String loadBalancingPolicy,
                                         @Qualifier("userResolver") SaigonParkingNameResolverProvider nameResolverProvider) {

        return ManagedChannelBuilder
                .forTarget("consul://" + host + ":" + port)                     // build channel to server with server's address
                .keepAliveWithoutCalls(false)                                   // Close channel when client has already received response
                .idleTimeout(timeout, TimeUnit.MILLISECONDS)                    // 10000 milliseconds / 1000 = 10 seconds --> request time-out
                .maxInboundMetadataSize(maxInBoundMetadataSize * 1024 * 1024)   // 2KB * 1024 = 2MB --> max message header size
                .maxInboundMessageSize(maxInBoundMessageSize * 1024 * 1024)     // 10KB * 1024 = 10MB --> max message size to transfer together
                .defaultLoadBalancingPolicy(loadBalancingPolicy)                // set load balancing policy for channel
                .nameResolverFactory(nameResolverProvider)                      // using Consul service discovery for DNS querying
                .intercept(clientInterceptor)                                   // add internal credential authentication
                .usePlaintext()                                                 // use plain-text to communicate internally
                .build();                                                       // Build channel to communicate over gRPC
    }


    /* asynchronous user service stub */
    @Bean
    public UserServiceGrpc.UserServiceStub userServiceStub(@Qualifier("userChannel") ManagedChannel channel) {
        return UserServiceGrpc.newStub(channel);
    }


    /* synchronous user service stub */
    @Bean
    public UserServiceGrpc.UserServiceBlockingStub userServiceBlockingStub(@Qualifier("userChannel") ManagedChannel channel) {
        return UserServiceGrpc.newBlockingStub(channel);
    }
}

// Node: repos/cloned_ms_repos/saigonparking/service/auth-service/src/main/java/com/bht/saigonparking/service/auth/configuration/ChannelConfiguration.java:ChannelConfiguration.<init>
// Node: __
// Node: Bean
// Node: userServiceNameResolverProvider
// Node: Value
// Node: SaigonParkingNameResolverProvider
// Node: newStub
// Node: newBlockingStub
// Node: managedChannel
// Node: Qualifier
// Node: forTarget
// Node: keepAliveWithoutCalls
// Node: idleTimeout
// Node: maxInboundMetadataSize
// Node: maxInboundMessageSize
// Node: defaultLoadBalancingPolicy
// Node: nameResolverFactory
// Node: intercept
// Node: usePlaintext
// Node: userServiceStub
// Node: userServiceBlockingStub
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

// Node: repos/cloned_ms_repos/saigonparking/service/auth-service/src/main/java/com/bht/saigonparking/service/auth/service/grpc/AuthServiceGrpcImpl.java:AuthServiceGrpcImpl.<init>
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

// Node: repos/cloned_ms_repos/saigonparking/service/auth-service/src/main/java/com/bht/saigonparking/service/auth/service/impl/AuthServiceHelperImpl.java:AuthServiceHelperImpl.<init>
package com.bht.saigonparking.service.parkinglot.configuration;

import java.util.concurrent.TimeUnit;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.client.discovery.DiscoveryClient;
import org.springframework.context.annotation.Bean;
import org.springframework.stereotype.Component;

import com.bht.saigonparking.api.grpc.user.UserServiceGrpc;
import com.bht.saigonparking.common.interceptor.SaigonParkingClientInterceptor;
import com.bht.saigonparking.common.loadbalance.SaigonParkingNameResolverProvider;

import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import lombok.AllArgsConstructor;

/**
 *
 * @author bht
 */
@Component
@AllArgsConstructor(onConstructor = @__(@Autowired))
public final class ChannelConfiguration {

    private final SaigonParkingClientInterceptor clientInterceptor;

    @Bean("userResolver")
    public SaigonParkingNameResolverProvider userServiceNameResolverProvider(@Value("${connection.user-service.id}") String serviceId,
                                                                             @Autowired DiscoveryClient discoveryClient) {
        return new SaigonParkingNameResolverProvider(serviceId, discoveryClient);
    }


    /**
     *
     * channel is the abstraction to connect to a service endpoint
     *
     * note for gRPC service stub:
     *      .newStub(channel)          --> nonblocking/asynchronous stub
     *      .newBlockingStub(channel)  --> blocking/synchronous stub
     */
    @Bean("userChannel")
    public ManagedChannel managedChannel(@Value("${spring.cloud.consul.host}") String host,
                                         @Value("${spring.cloud.consul.port}") int port,
                                         @Value("${connection.idle-timeout}") int timeout,
                                         @Value("${connection.max-inbound-message-size}") int maxInBoundMessageSize,
                                         @Value("${connection.max-inbound-metadata-size}") int maxInBoundMetadataSize,
                                         @Value("${connection.load-balancing-policy}") String loadBalancingPolicy,
                                         @Qualifier("userResolver") SaigonParkingNameResolverProvider nameResolverProvider) {

        return ManagedChannelBuilder
                .forTarget("consul://" + host + ":" + port)                     // build channel to server with server's address
                .keepAliveWithoutCalls(false)                                   // Close channel when client has already received response
                .idleTimeout(timeout, TimeUnit.MILLISECONDS)                    // 10000 milliseconds / 1000 = 10 seconds --> request time-out
                .maxInboundMetadataSize(maxInBoundMetadataSize * 1024 * 1024)   // 2KB * 1024 = 2MB --> max message header size
                .maxInboundMessageSize(maxInBoundMessageSize * 1024 * 1024)     // 10KB * 1024 = 10MB --> max message size to transfer together
                .defaultLoadBalancingPolicy(loadBalancingPolicy)                // set load balancing policy for channel
                .nameResolverFactory(nameResolverProvider)                      // using Consul service discovery for DNS querying
                .intercept(clientInterceptor)                                   // add internal credential authentication
                .usePlaintext()                                                 // use plain-text to communicate internally
                .build();                                                       // Build channel to communicate over gRPC
    }


    /* asynchronous user service stub */
    @Bean
    public UserServiceGrpc.UserServiceStub userServiceStub(@Qualifier("userChannel") ManagedChannel channel) {
        return UserServiceGrpc.newStub(channel);
    }


    /* synchronous user service stub */
    @Bean
    public UserServiceGrpc.UserServiceBlockingStub userServiceBlockingStub(@Qualifier("userChannel") ManagedChannel channel) {
        return UserServiceGrpc.newBlockingStub(channel);
    }
}

// Node: repos/cloned_ms_repos/saigonparking/service/parkinglot-service/src/main/java/com/bht/saigonparking/service/parkinglot/configuration/ChannelConfiguration.java:ChannelConfiguration.<init>
package com.bht.saigonparking.service.parkinglot.configuration;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.stereotype.Component;

import com.amazonaws.auth.AWSCredentialsProvider;
import com.amazonaws.auth.AWSStaticCredentialsProvider;
import com.amazonaws.auth.BasicAWSCredentials;
import com.amazonaws.services.s3.AmazonS3;
import com.amazonaws.services.s3.AmazonS3ClientBuilder;

/**
 *
 * @author bht
 */
@Component
public final class AwsConfiguration {

    @Bean("bucketName")
    public String getBucketName(@Value("${aws.bucket}") String bucketName) {
        return bucketName;
    }

    @Bean
    public AWSCredentialsProvider getAWSCredentials(@Value("${aws.access.key.id}") String awsKeyId,
                                                    @Value("${aws.access.key.secret}") String awsKeySecret) {
        return new AWSStaticCredentialsProvider(
                new BasicAWSCredentials(awsKeyId, awsKeySecret));
    }

    @Bean
    public AmazonS3 amazonS3Client(AWSCredentialsProvider awsCredentialsProvider,
                                   @Value("${aws.region}") String awsRegion) {
        return AmazonS3ClientBuilder.standard()
                .withCredentials(awsCredentialsProvider)
                .withRegion(awsRegion)
                .build();
    }
}

// Node: repos/cloned_ms_repos/saigonparking/service/parkinglot-service/src/main/java/com/bht/saigonparking/service/parkinglot/configuration/AwsConfiguration.java:AwsConfiguration.<init>
// Node: getBucketName
// Node: getAWSCredentials
// Node: AWSStaticCredentialsProvider
// Node: BasicAWSCredentials
// Node: amazonS3Client
// Node: standard
// Node: withCredentials
// Node: withRegion
// Node: Mapper
package com.bht.saigonparking.service.parkinglot.mapper;

import java.util.HashMap;
import java.util.Map;
import java.util.stream.Collectors;

import javax.persistence.EntityNotFoundException;
import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;

import org.mapstruct.Mapper;
import org.mapstruct.Named;
import org.mapstruct.NullValueMappingStrategy;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import com.bht.saigonparking.api.grpc.parkinglot.ParkingLotType;
import com.bht.saigonparking.common.base.BaseBean;
import com.bht.saigonparking.service.parkinglot.configuration.AppConfiguration;
import com.bht.saigonparking.service.parkinglot.entity.ParkingLotTypeEntity;
import com.bht.saigonparking.service.parkinglot.repository.core.ParkingLotTypeRepository;
import com.google.common.collect.BiMap;
import com.google.common.collect.HashBiMap;

import lombok.Setter;

/**
 *
 * this class is self-customized mapper for all enums, include:
 *      + UserRole:       3 role --> ADMIN, CUSTOMER, PARKING_LOT_EMPLOYEE
 *      + ParkingLotType: 3 type --> PRIVATE, BUILDING, STREET
 *
 * for using repository inside Component class,
 * we need to {@code @Autowired} it by Spring Dependency Injection
 * we can achieve that easily
 * by using {@code @Setter(onMethod = @__(@Autowired)} for class level like below
 *
 * we cannot use {@code @AllArgsConstructor} for class level,
 * because these repository/injected fields are optional,
 * and it will conflict with {@code @Mapper @Component} bean
 * which will be initialized by NonArgsConstructor !!!!!!!!!
 *
 * @author bht
 */
@Component
@Setter(onMethod = @__(@Autowired))
@Mapper(componentModel = "spring",
        implementationPackage = AppConfiguration.BASE_PACKAGE + ".mapper.impl",
        nullValueMappingStrategy = NullValueMappingStrategy.RETURN_DEFAULT)
public abstract class EnumMapper implements BaseBean {

    private ParkingLotTypeRepository parkingLotTypeRepository;
    private static final BiMap<ParkingLotTypeEntity, ParkingLotType> PARKING_LOT_TYPE_BI_MAP = HashBiMap.create();
    private static final Map<Long, ParkingLotType> PARKING_LOT_TYPE_MAP = new HashMap<>();
    private static final Map<Long, Long> PARKING_LOT_TYPE_VALUE_MAP = new HashMap<>();

    @Override
    public void initialize() {
        initParkingLotTypeBiMap();
        initParkingLotTypeValueMap();
        initParkingLotTypeMap();
    }

    @Named("toParkingLotType")
    public ParkingLotType toParkingLotType(@NotNull ParkingLotTypeEntity parkingLotTypeEntity) {
        return PARKING_LOT_TYPE_BI_MAP.get(parkingLotTypeEntity);
    }

    @Named("toParkingLotTypeEntity")
    public ParkingLotTypeEntity toParkingLotTypeEntity(@NotNull ParkingLotType parkingLotType) {
        return PARKING_LOT_TYPE_BI_MAP.inverse().get(parkingLotType);
    }


    @Named("toParkingLotTypeFromId")
    public ParkingLotType toParkingLotType(@NotNull Long parkingLotTypeId) {
        return PARKING_LOT_TYPE_MAP.get(parkingLotTypeId);
    }

    @Named("toParkingLotTypeValue")
    public Long toParkingLotTypeValue(Long parkingLotTypeId) {
        return PARKING_LOT_TYPE_VALUE_MAP.get(parkingLotTypeId);
    }

    private void initParkingLotTypeBiMap() {
        PARKING_LOT_TYPE_BI_MAP.put(getParkingLotTypeByType("PRIVATE"), ParkingLotType.PRIVATE);
        PARKING_LOT_TYPE_BI_MAP.put(getParkingLotTypeByType("BUILDING"), ParkingLotType.BUILDING);
        PARKING_LOT_TYPE_BI_MAP.put(getParkingLotTypeByType("STREET"), ParkingLotType.STREET);
    }

    private void initParkingLotTypeValueMap() {
        PARKING_LOT_TYPE_VALUE_MAP.putAll(PARKING_LOT_TYPE_BI_MAP.entrySet().stream()
                .collect(Collectors.toMap(entry -> entry.getKey().getId(), entry -> (long) entry.getValue().getNumber())));
    }

    private void initParkingLotTypeMap() {
        PARKING_LOT_TYPE_MAP.put(PARKING_LOT_TYPE_BI_MAP.inverse().get(ParkingLotType.PRIVATE).getId(), ParkingLotType.PRIVATE);
        PARKING_LOT_TYPE_MAP.put(PARKING_LOT_TYPE_BI_MAP.inverse().get(ParkingLotType.BUILDING).getId(), ParkingLotType.BUILDING);
        PARKING_LOT_TYPE_MAP.put(PARKING_LOT_TYPE_BI_MAP.inverse().get(ParkingLotType.STREET).getId(), ParkingLotType.STREET);
    }

    private ParkingLotTypeEntity getParkingLotTypeByType(@NotEmpty String type) {
        return parkingLotTypeRepository.findByType(type).orElseThrow(EntityNotFoundException::new);
    }
}

// Node: repos/cloned_ms_repos/saigonparking/service/parkinglot-service/src/main/java/com/bht/saigonparking/service/parkinglot/mapper/EnumMapper.java:is.<init>
// Node: Setter
// Node: create
package com.bht.saigonparking.service.parkinglot.mapper;

import java.sql.Time;
import java.sql.Timestamp;

import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;

import org.mapstruct.Mapper;
import org.mapstruct.Named;
import org.mapstruct.NullValueMappingStrategy;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import com.bht.saigonparking.api.grpc.parkinglot.ParkingLotInformation;
import com.bht.saigonparking.api.grpc.parkinglot.ParkingLotType;
import com.bht.saigonparking.common.util.ImageUtil;
import com.bht.saigonparking.service.parkinglot.configuration.AppConfiguration;
import com.bht.saigonparking.service.parkinglot.service.extra.ImageService;
import com.google.protobuf.ByteString;

import lombok.Setter;

/**
 *
 * Mapper for the others & default object of each type
 *
 * Note that customized class and all of
 * its attributes, its methods should be declared as non-public
 * in order to hide this class and its methods, its attributes
 * from outside of mapper package
 *
 * @author bht
 */
@Component
@Setter(onMethod = @__(@Autowired))
@Mapper(componentModel = "spring",
        implementationPackage = AppConfiguration.BASE_PACKAGE + ".mapper.impl",
        nullValueMappingStrategy = NullValueMappingStrategy.RETURN_DEFAULT)
public abstract class CustomizedMapper {

    private ImageService imageService;

    public static final String DEFAULT_STRING_VALUE = "";
    public static final Short DEFAULT_SHORT_VALUE = 0;
    public static final Integer DEFAULT_INT_VALUE = 0;
    public static final Long DEFAULT_LONG_VALUE = 0L;
    public static final Double DEFAULT_DOUBLE_VALUE = 0.0;
    public static final Boolean DEFAULT_BOOL_VALUE = Boolean.FALSE;
    public static final ByteString DEFAULT_BYTE_STRING_VALUE = ByteString.EMPTY;

    public static final ParkingLotType DEFAULT_PARKING_LOT_TYPE = ParkingLotType.UNRECOGNIZED;
    public static final ParkingLotInformation DEFAULT_PARKING_LOT_INFORMATION = ParkingLotInformation.getDefaultInstance();

    @Named("toTimeString")
    public String toTimeString(@NotNull Time time) {
        return time.toString();
    }

    @Named("toTime")
    public Time toTime(@NotEmpty String timeString) {
        return Time.valueOf(timeString);
    }

    @Named("toTimestampString")
    public String toTimestampString(@NotNull Timestamp timestamp) {
        return timestamp.toString();
    }

    @Named("toTimestamp")
    public Timestamp toTimestamp(@NotEmpty String timestampString) {
        return Timestamp.valueOf(timestampString);
    }

    @Named("toEncodedParkingLotImage")
    public ByteString toEncodedParkingLotImage(@NotNull Integer parkingLotId) {
        return ImageUtil.encodeImage(imageService.getImage(
                "plot" + parkingLotId, ImageService.ImageExtension.JPG));
    }
}

// Node: repos/cloned_ms_repos/saigonparking/service/parkinglot-service/src/main/java/com/bht/saigonparking/service/parkinglot/mapper/CustomizedMapper.java:and.<init>
package com.bht.saigonparking.service.parkinglot.mapper;

import java.util.Collections;

import javax.persistence.EntityNotFoundException;
import javax.validation.constraints.NotNull;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import com.bht.saigonparking.api.grpc.parkinglot.ParkingLot;
import com.bht.saigonparking.api.grpc.parkinglot.ParkingLotInformation;
import com.bht.saigonparking.service.parkinglot.entity.ParkingLotEntity;
import com.bht.saigonparking.service.parkinglot.entity.ParkingLotInformationEntity;
import com.bht.saigonparking.service.parkinglot.entity.ParkingLotLimitEntity;
import com.bht.saigonparking.service.parkinglot.repository.core.ParkingLotRepository;

import lombok.AllArgsConstructor;

/**
 *
 * @author bht
 */
@Component
@AllArgsConstructor(onConstructor = @__(@Autowired))
public final class ParkingLotMapperExtImpl implements ParkingLotMapperExt {

    private final EnumMapper enumMapper;
    private final CustomizedMapper customizedMapper;
    private final ParkingLotRepository parkingLotRepository;

    @Override
    public final ParkingLotEntity toParkingLotEntity(@NotNull ParkingLot parkingLot, boolean isAboutToCreate) {

        ParkingLotEntity parkingLotEntity;
        ParkingLotLimitEntity parkingLotLimitEntity;
        ParkingLotInformationEntity parkingLotInformationEntity;

        if (!isAboutToCreate) {

            /* case: update parkingLotEntity */
            parkingLotEntity = parkingLotRepository.getById(parkingLot.getId()).orElseThrow(EntityNotFoundException::new);
            parkingLotLimitEntity = parkingLotEntity.getParkingLotLimitEntity();
            parkingLotInformationEntity = parkingLotEntity.getParkingLotInformationEntity();
            parkingLotEntity.setVersion(parkingLot.getVersion());

            parkingLotLimitEntity.setTotalSlot((short) parkingLot.getTotalSlot());
            parkingLotLimitEntity.setAvailableSlot((short) parkingLot.getAvailableSlot());

            ParkingLotInformation parkingLotInformation = parkingLot.getInformation();
            parkingLotInformationEntity.setName(parkingLotInformation.getName());
            parkingLotInformationEntity.setAddress(parkingLotInformation.getAddress());
            parkingLotInformationEntity.setPhone(parkingLotInformation.getPhone().isEmpty() ? "" : parkingLotInformation.getPhone());

        } else {

            /* case: create parkingLotEntity */
            parkingLotEntity = new ParkingLotEntity();
            parkingLotEntity.setVersion(1L);
            parkingLotEntity.setParkingLotUnitEntitySet(Collections.emptySet());
            parkingLotEntity.setParkingLotEmployeeEntitySet(Collections.emptySet());
            parkingLotEntity.setParkingLotTypeEntity(enumMapper.toParkingLotTypeEntity(parkingLot.getType()));
        }

        parkingLotEntity.setLatitude(parkingLot.getLatitude());
        parkingLotEntity.setLongitude(parkingLot.getLongitude());
        parkingLotEntity.setOpeningHour(customizedMapper.toTime(parkingLot.getOpeningHour()));
        parkingLotEntity.setClosingHour(customizedMapper.toTime(parkingLot.getClosingHour()));

        return parkingLotEntity;
    }
}

// Node: repos/cloned_ms_repos/saigonparking/service/parkinglot-service/src/main/java/com/bht/saigonparking/service/parkinglot/mapper/ParkingLotMapperExtImpl.java:ParkingLotMapperExtImpl.<init>
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

// Node: repos/cloned_ms_repos/saigonparking/service/parkinglot-service/src/main/java/com/bht/saigonparking/service/parkinglot/service/grpc/ParkingLotServiceGrpcImpl.java:implements.<init>
package com.bht.saigonparking.service.parkinglot.service.extra.impl;

import java.io.IOException;
import java.io.InputStream;

import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.bht.saigonparking.service.parkinglot.service.extra.ImageService;
import com.bht.saigonparking.service.parkinglot.service.extra.S3Service;
import com.google.common.io.ByteStreams;
import com.google.protobuf.Internal;

import lombok.AllArgsConstructor;

/**
 *
 * this class implements all services relevant to processing image store on S3
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
public class ImageServiceImpl implements ImageService {

    private final S3Service s3Service;


    private static String toImagePath(@NotEmpty String pathFromGalleryDir, @NotNull ImageService.ImageExtension fileExtension) {
        return "gallery/" + pathFromGalleryDir + '.' + fileExtension.getExtension();
    }

    @Override
    public byte[] getImage(@NotEmpty String pathFromGalleryDir, @NotNull ImageService.ImageExtension fileExtension) {
        try (InputStream inputStream = s3Service.getFile(toImagePath(pathFromGalleryDir, fileExtension), false)) {
            return (inputStream != null) ? ByteStreams.toByteArray(inputStream) : Internal.EMPTY_BYTE_ARRAY;

        } catch (IOException e) {
            return Internal.EMPTY_BYTE_ARRAY;
        }
    }

    @Override
    public void saveImage(byte[] imageData, @NotEmpty String pathFromGalleryDir, @NotNull ImageService.ImageExtension fileExtension) {
        if (imageData != null && imageData.length > 0) {
            s3Service.saveFile(imageData, toImagePath(pathFromGalleryDir, fileExtension), true);
        }
    }

    @Override
    public void deleteImage(@NotEmpty String pathFromGalleryDir, @NotNull ImageService.ImageExtension fileExtension) {
        s3Service.deleteFile(toImagePath(pathFromGalleryDir, fileExtension), true);
    }
}

// Node: repos/cloned_ms_repos/saigonparking/service/parkinglot-service/src/main/java/com/bht/saigonparking/service/parkinglot/service/extra/impl/ImageServiceImpl.java:implements.<init>
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

// Node: repos/cloned_ms_repos/saigonparking/service/parkinglot-service/src/main/java/com/bht/saigonparking/service/parkinglot/service/extra/impl/S3ServiceImpl.java:implements.<init>
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

// Node: repos/cloned_ms_repos/saigonparking/service/parkinglot-service/src/main/java/com/bht/saigonparking/service/parkinglot/service/main/impl/ParkingLotServiceImpl.java:implements.<init>
package com.bht.saigonparking.service.user.configuration;

import java.util.concurrent.TimeUnit;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.client.discovery.DiscoveryClient;
import org.springframework.context.annotation.Bean;
import org.springframework.stereotype.Component;

import com.bht.saigonparking.api.grpc.parkinglot.ParkingLotServiceGrpc;
import com.bht.saigonparking.common.interceptor.SaigonParkingClientInterceptor;
import com.bht.saigonparking.common.loadbalance.SaigonParkingNameResolverProvider;

import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import lombok.AllArgsConstructor;

/**
 *
 * @author bht
 */
@Component
@AllArgsConstructor(onConstructor = @__(@Autowired))
public final class ChannelConfiguration {

    private final SaigonParkingClientInterceptor clientInterceptor;

    @Bean("parkingLotResolver")
    public SaigonParkingNameResolverProvider userServiceNameResolver(@Value("${connection.parkinglot-service.id}") String serviceId,
                                                                     @Autowired DiscoveryClient discoveryClient) {

        return new SaigonParkingNameResolverProvider(serviceId, discoveryClient);
    }

    /**
     *
     * channel is the abstraction to connect to a service endpoint
     *
     * note for gRPC service stub:
     *      .newStub(channel)          --> nonblocking/asynchronous stub
     *      .newBlockingStub(channel)  --> blocking/synchronous stub
     */
    @Bean("parkingLotChannel")
    public ManagedChannel parkingLotChannel(@Value("${spring.cloud.consul.host}") String host,
                                            @Value("${spring.cloud.consul.port}") int port,
                                            @Value("${connection.idle-timeout}") int timeout,
                                            @Value("${connection.max-inbound-message-size}") int maxInBoundMessageSize,
                                            @Value("${connection.max-inbound-metadata-size}") int maxInBoundMetadataSize,
                                            @Value("${connection.load-balancing-policy}") String loadBalancingPolicy,
                                            @Qualifier("parkingLotResolver") SaigonParkingNameResolverProvider nameResolverProvider) {

        return ManagedChannelBuilder
                .forTarget("consul://" + host + ":" + port)                     // build channel to server with server's address
                .keepAliveWithoutCalls(false)                                   // Close channel when client has already received response
                .idleTimeout(timeout, TimeUnit.MILLISECONDS)                    // 10000 milliseconds / 1000 = 10 seconds --> request time-out
                .maxInboundMetadataSize(maxInBoundMetadataSize * 1024 * 1024)   // 2KB * 1024 = 2MB --> max message header size
                .maxInboundMessageSize(maxInBoundMessageSize * 1024 * 1024)     // 10KB * 1024 = 10MB --> max message size to transfer together
                .defaultLoadBalancingPolicy(loadBalancingPolicy)                // set load balancing policy for channel
                .nameResolverFactory(nameResolverProvider)                      // using Consul service discovery for DNS querying
                .intercept(clientInterceptor)                                   // add internal credential authentication
                .usePlaintext()                                                 // use plain-text to communicate internally
                .build();                                                       // Build channel to communicate over gRPC
    }


    /* asynchronous parking-lot service stub */
    @Bean
    public ParkingLotServiceGrpc.ParkingLotServiceStub parkingLotServiceStub(@Qualifier("parkingLotChannel") ManagedChannel channel) {
        return ParkingLotServiceGrpc.newStub(channel);
    }


    /* synchronous parking-lot service stub */
    @Bean
    public ParkingLotServiceGrpc.ParkingLotServiceBlockingStub parkingLotServiceBlockingStub(@Qualifier("parkingLotChannel") ManagedChannel channel) {
        return ParkingLotServiceGrpc.newBlockingStub(channel);
    }
}

// Node: repos/cloned_ms_repos/saigonparking/service/user-service/src/main/java/com/bht/saigonparking/service/user/configuration/ChannelConfiguration.java:ChannelConfiguration.<init>
// Node: userServiceNameResolver
// Node: parkingLotChannel
// Node: parkingLotServiceStub
// Node: parkingLotServiceBlockingStub
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

// Node: repos/cloned_ms_repos/saigonparking/service/user-service/src/main/java/com/bht/saigonparking/service/user/configuration/MessageQueueConfiguration.java:MessageQueueConfiguration.<init>
// Node: RabbitListener
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

// Node: repos/cloned_ms_repos/saigonparking/service/user-service/src/main/java/com/bht/saigonparking/service/user/mapper/UserMapperExtImpl.java:UserMapperExtImpl.<init>
// Node: encode
package com.bht.saigonparking.service.user.mapper;

import java.util.HashMap;
import java.util.Map;
import java.util.stream.Collectors;

import javax.persistence.EntityNotFoundException;
import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;

import org.mapstruct.Mapper;
import org.mapstruct.Named;
import org.mapstruct.NullValueMappingStrategy;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import com.bht.saigonparking.api.grpc.user.UserRole;
import com.bht.saigonparking.common.base.BaseBean;
import com.bht.saigonparking.service.user.configuration.AppConfiguration;
import com.bht.saigonparking.service.user.entity.UserRoleEntity;
import com.bht.saigonparking.service.user.repository.core.UserRoleRepository;
import com.google.common.collect.BiMap;
import com.google.common.collect.HashBiMap;

import lombok.Setter;

/**
 *
 * this class is self-customized mapper for all enums, include:
 *      + UserRole:       4 role --> ADMIN, CUSTOMER, PARKING_LOT_EMPLOYEE, GOVERNMENT_EMPLOYEE
 *
 * for using repository inside Component class,
 * we need to {@code @Autowired} it by Spring Dependency Injection
 * we can achieve that easily
 * by using {@code @Setter(onMethod = @__(@Autowired)} for class level like below
 *
 * we cannot use {@code @AllArgsConstructor} for class level,
 * because these repository/injected fields are optional,
 * and it will conflict with {@code @Mapper @Component} bean
 * which will be initialized by NonArgsConstructor !!!!!!!!!
 *
 * @author bht
 */
@Component
@Setter(onMethod = @__(@Autowired))
@Mapper(componentModel = "spring",
        implementationPackage = AppConfiguration.BASE_PACKAGE + ".mapper.impl",
        nullValueMappingStrategy = NullValueMappingStrategy.RETURN_DEFAULT)
public abstract class EnumMapper implements BaseBean {

    private UserRoleRepository userRoleRepository;
    private static final BiMap<UserRoleEntity, UserRole> USER_ROLE_BI_MAP = HashBiMap.create();
    private static final Map<Long, Long> USER_ROLE_VALUE_MAP = new HashMap<>();

    @Override
    public void initialize() {
        initUserRoleBiMap();
        initUserRoleValueMap();
    }

    @Named("toUserRole")
    public UserRole toUserRole(@NotNull UserRoleEntity userRoleEntity) {
        return USER_ROLE_BI_MAP.get(userRoleEntity);
    }

    @Named("toUserRoleEntity")
    public UserRoleEntity toUserRoleEntity(@NotNull UserRole userRole) {
        return USER_ROLE_BI_MAP.inverse().get(userRole);
    }

    @Named("toUserRoleValue")
    public Long toUserRoleValue(Long userRoleId) {
        return USER_ROLE_VALUE_MAP.get(userRoleId);
    }

    private void initUserRoleBiMap() {
        USER_ROLE_BI_MAP.put(getUserRoleByRoleName("ADMIN"), UserRole.ADMIN);
        USER_ROLE_BI_MAP.put(getUserRoleByRoleName("CUSTOMER"), UserRole.CUSTOMER);
        USER_ROLE_BI_MAP.put(getUserRoleByRoleName("PARKING_LOT_EMPLOYEE"), UserRole.PARKING_LOT_EMPLOYEE);
        USER_ROLE_BI_MAP.put(getUserRoleByRoleName("GOVERNMENT"), UserRole.GOVERNMENT_EMPLOYEE);
    }

    private void initUserRoleValueMap() {
        USER_ROLE_VALUE_MAP.putAll(USER_ROLE_BI_MAP.entrySet().stream()
                .collect(Collectors.toMap(entry -> entry.getKey().getId(), entry -> (long) entry.getValue().getNumber())));
    }

    private UserRoleEntity getUserRoleByRoleName(@NotEmpty String role) {
        return userRoleRepository.findByRole(role).orElseThrow(EntityNotFoundException::new);
    }
}

// Node: repos/cloned_ms_repos/saigonparking/service/user-service/src/main/java/com/bht/saigonparking/service/user/mapper/EnumMapper.java:is.<init>
package com.bht.saigonparking.service.user.mapper;

import java.sql.Time;
import java.sql.Timestamp;

import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;

import org.mapstruct.Mapper;
import org.mapstruct.Named;
import org.mapstruct.NullValueMappingStrategy;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import com.bht.saigonparking.api.grpc.user.Customer;
import com.bht.saigonparking.api.grpc.user.User;
import com.bht.saigonparking.api.grpc.user.UserRole;
import com.bht.saigonparking.service.user.configuration.AppConfiguration;
import com.google.protobuf.ByteString;

import lombok.Setter;

/**
 *
 * Mapper for the others & default object of each type
 *
 * Note that customized class and all of
 * its attributes, its methods are declared as non-public
 * in order to hide this class and its methods, its attributes
 * from outside of mapper package
 *
 * It is expected to be seen only by mapper class
 *
 * @author bht
 */
@Component
@Setter(onMethod = @__(@Autowired))
@Mapper(componentModel = "spring",
        implementationPackage = AppConfiguration.BASE_PACKAGE + ".mapper.impl",
        nullValueMappingStrategy = NullValueMappingStrategy.RETURN_DEFAULT)
public abstract class CustomizedMapper {

    public static final String DEFAULT_STRING_VALUE = "";
    public static final Short DEFAULT_SHORT_VALUE = 0;
    public static final Integer DEFAULT_INT_VALUE = 0;
    public static final Long DEFAULT_LONG_VALUE = 0L;
    public static final Double DEFAULT_DOUBLE_VALUE = 0.0;
    public static final Boolean DEFAULT_BOOL_VALUE = Boolean.FALSE;
    public static final ByteString DEFAULT_BYTE_STRING_VALUE = ByteString.EMPTY;

    public static final UserRole DEFAULT_USER_ROLE = UserRole.UNRECOGNIZED;
    public static final User DEFAULT_USER = User.getDefaultInstance();
    public static final Customer DEFAULT_CUSTOMER = Customer.getDefaultInstance();

    @Named("toTimeString")
    public String toTimeString(@NotNull Time time) {
        return time.toString();
    }

    @Named("toTime")
    public Time toTime(@NotEmpty String timeString) {
        return Time.valueOf(timeString);
    }

    @Named("toTimestampString")
    public String toTimestampString(@NotNull Timestamp timestamp) {
        return timestamp.toString();
    }

    @Named("toTimestamp")
    public Timestamp toTimestamp(@NotEmpty String timestampString) {
        return Timestamp.valueOf(timestampString);
    }
}

// Node: repos/cloned_ms_repos/saigonparking/service/user-service/src/main/java/com/bht/saigonparking/service/user/mapper/CustomizedMapper.java:and.<init>
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

// Node: repos/cloned_ms_repos/saigonparking/service/user-service/src/main/java/com/bht/saigonparking/service/user/service/grpc/UserServiceGrpcImpl.java:implements.<init>
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

// Node: repos/cloned_ms_repos/saigonparking/service/user-service/src/main/java/com/bht/saigonparking/service/user/service/main/impl/UserServiceImpl.java:implements.<init>
package com.bht.saigonparking.service.booking.configuration;

import java.util.concurrent.TimeUnit;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.client.discovery.DiscoveryClient;
import org.springframework.context.annotation.Bean;
import org.springframework.stereotype.Component;

import com.bht.saigonparking.api.grpc.parkinglot.ParkingLotServiceGrpc;
import com.bht.saigonparking.api.grpc.user.UserServiceGrpc;
import com.bht.saigonparking.common.interceptor.SaigonParkingClientInterceptor;
import com.bht.saigonparking.common.loadbalance.SaigonParkingNameResolverProvider;

import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import lombok.AllArgsConstructor;

/**
 *
 * @author bht
 */
@Component
@AllArgsConstructor(onConstructor = @__(@Autowired))
public final class ChannelConfiguration {

    private final SaigonParkingClientInterceptor clientInterceptor;

    @Bean("parkingLotResolver")
    public SaigonParkingNameResolverProvider userServiceNameResolver(@Value("${connection.parkinglot-service.id}") String serviceId,
                                                                     @Autowired DiscoveryClient discoveryClient) {

        return new SaigonParkingNameResolverProvider(serviceId, discoveryClient);
    }

    /**
     *
     * channel is the abstraction to connect to a service endpoint
     *
     * note for gRPC service stub:
     *      .newStub(channel)          --> nonblocking/asynchronous stub
     *      .newBlockingStub(channel)  --> blocking/synchronous stub
     */
    @Bean("parkingLotChannel")
    public ManagedChannel parkingLotChannel(@Value("${spring.cloud.consul.host}") String host,
                                            @Value("${spring.cloud.consul.port}") int port,
                                            @Value("${connection.idle-timeout}") int timeout,
                                            @Value("${connection.max-inbound-message-size}") int maxInBoundMessageSize,
                                            @Value("${connection.max-inbound-metadata-size}") int maxInBoundMetadataSize,
                                            @Value("${connection.load-balancing-policy}") String loadBalancingPolicy,
                                            @Qualifier("parkingLotResolver") SaigonParkingNameResolverProvider nameResolverProvider) {

        return ManagedChannelBuilder
                .forTarget("consul://" + host + ":" + port)                     // build channel to server with server's address
                .keepAliveWithoutCalls(false)                                   // Close channel when client has already received response
                .idleTimeout(timeout, TimeUnit.MILLISECONDS)                    // 10000 milliseconds / 1000 = 10 seconds --> request time-out
                .maxInboundMetadataSize(maxInBoundMetadataSize * 1024 * 1024)   // 2KB * 1024 = 2MB --> max message header size
                .maxInboundMessageSize(maxInBoundMessageSize * 1024 * 1024)     // 10KB * 1024 = 10MB --> max message size to transfer together
                .defaultLoadBalancingPolicy(loadBalancingPolicy)                // set load balancing policy for channel
                .nameResolverFactory(nameResolverProvider)                      // using Consul service discovery for DNS querying
                .intercept(clientInterceptor)                                   // add internal credential authentication
                .usePlaintext()                                                 // use plain-text to communicate internally
                .build();                                                       // Build channel to communicate over gRPC
    }

    /* asynchronous parking-lot service stub */
    @Bean
    public ParkingLotServiceGrpc.ParkingLotServiceStub parkingLotServiceStub(@Qualifier("parkingLotChannel") ManagedChannel channel) {
        return ParkingLotServiceGrpc.newStub(channel);
    }

    /* synchronous parking-lot service stub */
    @Bean
    public ParkingLotServiceGrpc.ParkingLotServiceBlockingStub parkingLotServiceBlockingStub(@Qualifier("parkingLotChannel") ManagedChannel channel) {
        return ParkingLotServiceGrpc.newBlockingStub(channel);
    }

    @Bean("userResolver")
    public SaigonParkingNameResolverProvider userServiceNameResolverProvider(@Value("${connection.user-service.id}") String serviceId,
                                                                             @Autowired DiscoveryClient discoveryClient) {

        return new SaigonParkingNameResolverProvider(serviceId, discoveryClient);
    }

    @Bean("userChannel")
    public ManagedChannel managedChannel(@Value("${spring.cloud.consul.host}") String host,
                                         @Value("${spring.cloud.consul.port}") int port,
                                         @Value("${connection.idle-timeout}") int timeout,
                                         @Value("${connection.max-inbound-message-size}") int maxInBoundMessageSize,
                                         @Value("${connection.max-inbound-metadata-size}") int maxInBoundMetadataSize,
                                         @Value("${connection.load-balancing-policy}") String loadBalancingPolicy,
                                         @Qualifier("userResolver") SaigonParkingNameResolverProvider nameResolverProvider) {

        return ManagedChannelBuilder
                .forTarget("consul://" + host + ":" + port)                     // build channel to server with server's address
                .keepAliveWithoutCalls(false)                                   // Close channel when client has already received response
                .idleTimeout(timeout, TimeUnit.MILLISECONDS)                    // 10000 milliseconds / 1000 = 10 seconds --> request time-out
                .maxInboundMetadataSize(maxInBoundMetadataSize * 1024 * 1024)   // 2KB * 1024 = 2MB --> max message header size
                .maxInboundMessageSize(maxInBoundMessageSize * 1024 * 1024)     // 10KB * 1024 = 10MB --> max message size to transfer together
                .defaultLoadBalancingPolicy(loadBalancingPolicy)                // set load balancing policy for channel
                .nameResolverFactory(nameResolverProvider)                      // using Consul service discovery for DNS querying
                .intercept(clientInterceptor)                                   // add internal credential authentication
                .usePlaintext()                                                 // use plain-text to communicate internally
                .build();                                                       // Build channel to communicate over gRPC
    }

    /* asynchronous user service stub */
    @Bean
    public UserServiceGrpc.UserServiceStub userServiceStub(@Qualifier("userChannel") ManagedChannel channel) {
        return UserServiceGrpc.newStub(channel);
    }

    /* synchronous user service stub */
    @Bean
    public UserServiceGrpc.UserServiceBlockingStub userServiceBlockingStub(@Qualifier("userChannel") ManagedChannel channel) {
        return UserServiceGrpc.newBlockingStub(channel);
    }
}

// Node: repos/cloned_ms_repos/saigonparking/service/booking-service/src/main/java/com/bht/saigonparking/service/booking/configuration/ChannelConfiguration.java:ChannelConfiguration.<init>
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

// Node: repos/cloned_ms_repos/saigonparking/service/booking-service/src/main/java/com/bht/saigonparking/service/booking/configuration/MessageQueueConfiguration.java:MessageQueueConfiguration.<init>
package com.bht.saigonparking.service.booking.mapper;

import java.util.HashMap;
import java.util.Map;
import java.util.stream.Collectors;

import javax.persistence.EntityNotFoundException;
import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;

import org.mapstruct.Mapper;
import org.mapstruct.Named;
import org.mapstruct.NullValueMappingStrategy;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import com.bht.saigonparking.api.grpc.booking.BookingStatus;
import com.bht.saigonparking.common.base.BaseBean;
import com.bht.saigonparking.service.booking.configuration.AppConfiguration;
import com.bht.saigonparking.service.booking.entity.BookingStatusEntity;
import com.bht.saigonparking.service.booking.repository.core.BookingStatusRepository;
import com.google.common.collect.BiMap;
import com.google.common.collect.HashBiMap;

import lombok.Setter;

/**
 *
 * for using repository inside Component class,
 * we need to {@code @Autowired} it by Spring Dependency Injection
 * we can achieve that easily
 * by using {@code @Setter(onMethod = @__(@Autowired)} for class level like below
 *
 * we cannot use {@code @AllArgsConstructor} for class level,
 * because these repository/injected fields are optional,
 * and it will conflict with {@code @Mapper @Component} bean
 * which will be initialized by NonArgsConstructor !!!!!!!!!
 *
 * @author bht
 */
@Component
@Setter(onMethod = @__(@Autowired))
@Mapper(componentModel = "spring",
        implementationPackage = AppConfiguration.BASE_PACKAGE + ".mapper.impl",
        nullValueMappingStrategy = NullValueMappingStrategy.RETURN_DEFAULT)
public abstract class EnumMapper implements BaseBean {

    private static final BiMap<BookingStatusEntity, BookingStatus> BOOKING_STATUS_BI_MAP = HashBiMap.create();
    private static final Map<Long, Long> BOOKING_STATUS_VALUE_MAP = new HashMap<>();
    private BookingStatusRepository bookingStatusRepository;

    @Override
    public void initialize() {
        initBookingStatusBiMap();
        initBookingStatusValueMap();
    }

    @Named("toBookingStatus")
    public BookingStatus toBookingStatus(@NotNull BookingStatusEntity bookingStatusEntity) {
        return BOOKING_STATUS_BI_MAP.get(bookingStatusEntity);
    }

    @Named("toBookingStatusEntity")
    public BookingStatusEntity toBookingStatusEntity(@NotNull BookingStatus bookingStatus) {
        return BOOKING_STATUS_BI_MAP.inverse().get(bookingStatus);
    }

    @Named("toBookingStatusValue")
    public Long toBookingStatusValue(Long bookingStatusId) {
        return BOOKING_STATUS_VALUE_MAP.get(bookingStatusId);
    }

    public BookingStatusEntity getDefaultBookingStatusEntity() {
        return toBookingStatusEntity(BookingStatus.CREATED);
    }

    private void initBookingStatusBiMap() {
        BOOKING_STATUS_BI_MAP.put(getBookingStatusByStatus("CREATED"), BookingStatus.CREATED);
        BOOKING_STATUS_BI_MAP.put(getBookingStatusByStatus("ACCEPTED"), BookingStatus.ACCEPTED);
        BOOKING_STATUS_BI_MAP.put(getBookingStatusByStatus("REJECTED"), BookingStatus.REJECTED);
        BOOKING_STATUS_BI_MAP.put(getBookingStatusByStatus("CANCELLED"), BookingStatus.CANCELLED);
        BOOKING_STATUS_BI_MAP.put(getBookingStatusByStatus("FINISHED"), BookingStatus.FINISHED);
    }

    private void initBookingStatusValueMap() {
        BOOKING_STATUS_VALUE_MAP.putAll(BOOKING_STATUS_BI_MAP.entrySet().stream()
                .collect(Collectors.toMap(entry -> entry.getKey().getId(), entry -> (long) entry.getValue().getNumber())));
    }

    private BookingStatusEntity getBookingStatusByStatus(@NotEmpty String status) {
        return bookingStatusRepository.findByStatus(status).orElseThrow(EntityNotFoundException::new);
    }
}

// Node: repos/cloned_ms_repos/saigonparking/service/booking-service/src/main/java/com/bht/saigonparking/service/booking/mapper/EnumMapper.java:level.<init>
package com.bht.saigonparking.service.booking.mapper;

import java.sql.Timestamp;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;

import org.mapstruct.Mapper;
import org.mapstruct.Named;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import com.bht.saigonparking.api.grpc.parkinglot.MapToParkingLotNameMapRequest;
import com.bht.saigonparking.api.grpc.parkinglot.ParkingLotServiceGrpc;
import com.bht.saigonparking.service.booking.configuration.AppConfiguration;
import com.bht.saigonparking.service.booking.entity.BookingEntity;
import com.fasterxml.uuid.Generators;
import com.google.protobuf.ByteString;
import com.google.protobuf.Int64Value;

import lombok.Setter;

/**
 *
 * Mapper for the others & default object of each type
 *
 * Note that customized class and all of
 * its attributes, its methods should be declared as non-public
 * in order to hide this class and its methods, its attributes
 * from outside of mapper package
 *
 * @author bht
 */
@Component
@Setter(onMethod = @__(@Autowired))
@Mapper(componentModel = "spring", implementationPackage = AppConfiguration.BASE_PACKAGE + ".mapper.impl")
public abstract class CustomizedMapper {

    public static final String DEFAULT_STRING_VALUE = "";
    public static final Short DEFAULT_SHORT_VALUE = 0;
    public static final Integer DEFAULT_INT_VALUE = 0;
    public static final Long DEFAULT_LONG_VALUE = 0L;
    public static final Double DEFAULT_DOUBLE_VALUE = 0.0;
    public static final Boolean DEFAULT_BOOL_VALUE = Boolean.FALSE;
    public static final ByteString DEFAULT_BYTE_STRING_VALUE = ByteString.EMPTY;

    private ParkingLotServiceGrpc.ParkingLotServiceBlockingStub parkingLotServiceBlockingStub;

    @Named("generateUUID")
    public UUID generateUUID() {
        return Generators.timeBasedGenerator().generate();
    }

    @Named("toUUIDString")
    public String toUUIDString(@NotNull UUID uuid) {
        return uuid.toString();
    }

    @Named("toTimestampString")
    public String toTimestampString(@NotNull Timestamp timestamp) {
        return timestamp.toString();
    }

    @Named("toTimestamp")
    public Timestamp toTimestamp(@NotEmpty String timestampString) {
        return Timestamp.valueOf(timestampString);
    }

    @Named("toParkingLotName")
    public String toParkingLotName(@NotNull Long parkingLotId) {
        return parkingLotServiceBlockingStub.getParkingLotNameByParkingLotId(Int64Value.of(parkingLotId)).getValue();
    }

    @Named("toBookingEntityParkingLotNameMap")
    public Map<BookingEntity, String> toBookingEntityParkingLotNameMap(@NotNull List<BookingEntity> bookingEntityList) {
        if (!bookingEntityList.isEmpty()) {
            Map<Long, String> parkingLotIdNameMap = parkingLotServiceBlockingStub
                    .mapToParkingLotNameMap(MapToParkingLotNameMapRequest.newBuilder()
                            .addAllParkingLotId(bookingEntityList.stream()
                                    .map(BookingEntity::getParkingLotId)
                                    .collect(Collectors.toList()))
                            .build())
                    .getParkingLotNameMap();

            return bookingEntityList.stream().collect(Collectors
                    .toMap(bookingEntity -> bookingEntity,
                            bookingEntity -> parkingLotIdNameMap.get(bookingEntity.getParkingLotId())));
        }
        return Collections.emptyMap();
    }
}

// Node: repos/cloned_ms_repos/saigonparking/service/booking-service/src/main/java/com/bht/saigonparking/service/booking/mapper/CustomizedMapper.java:and.<init>
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

// Node: repos/cloned_ms_repos/saigonparking/service/booking-service/src/main/java/com/bht/saigonparking/service/booking/service/grpc/BookingServiceGrpcImpl.java:BookingServiceGrpcImpl.<init>
// Node: RequiredArgsConstructor
// Node: encodeContents
package com.bht.saigonparking.service.booking.service.main;

import java.io.IOException;

import com.bht.saigonparking.common.annotation.UuidStringValidation;
import com.google.zxing.WriterException;

/**
 *
 * @author bht
 */
public interface QrCodeService {

    byte[] encodeContents(@UuidStringValidation String contents) throws WriterException, IOException;
}

// Node: repos/cloned_ms_repos/saigonparking/service/booking-service/src/main/java/com/bht/saigonparking/service/booking/service/main/QrCodeService.java:QrCodeService.<init>
package com.bht.saigonparking.service.booking.service.main.impl;

import java.io.ByteArrayOutputStream;
import java.io.IOException;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import com.bht.saigonparking.common.annotation.UuidStringValidation;
import com.bht.saigonparking.service.booking.service.main.QrCodeService;
import com.google.protobuf.Internal;
import com.google.zxing.BarcodeFormat;
import com.google.zxing.WriterException;
import com.google.zxing.client.j2se.MatrixToImageWriter;
import com.google.zxing.common.BitMatrix;
import com.google.zxing.qrcode.QRCodeWriter;

import lombok.RequiredArgsConstructor;

/**
 *
 * @author bht
 */
@Service
@RequiredArgsConstructor(onConstructor = @__(@Autowired))
public final class QrCodeServiceImpl implements QrCodeService {

    private final QRCodeWriter qrCodeWriter;

    @Value("${qr-code.width}")
    private Integer qrCodeWidth;

    @Value("${qr-code.height}")
    private Integer qrCodeHeight;

    @Override
    public byte[] encodeContents(@UuidStringValidation String contents) throws WriterException, IOException {
        if (!contents.isEmpty()) {
            ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream();
            BitMatrix bitMatrix = qrCodeWriter.encode(contents, BarcodeFormat.QR_CODE, qrCodeWidth, qrCodeHeight);
            MatrixToImageWriter.writeToStream(bitMatrix, "PNG", byteArrayOutputStream);
            return byteArrayOutputStream.toByteArray();
        }
        return Internal.EMPTY_BYTE_ARRAY;
    }
}

// Node: repos/cloned_ms_repos/saigonparking/service/booking-service/src/main/java/com/bht/saigonparking/service/booking/service/main/impl/QrCodeServiceImpl.java:QrCodeServiceImpl.<init>
// Node: ByteArrayOutputStream
// Node: writeToStream
package com.bht.saigonparking.service.booking.service.main.impl;

import static com.bht.saigonparking.api.grpc.booking.BookingStatus.CREATED;
import static com.bht.saigonparking.api.grpc.booking.BookingStatus.FINISHED;

import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;

import javax.persistence.EntityNotFoundException;
import javax.persistence.Tuple;
import javax.validation.constraints.Max;
import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;

import org.hibernate.validator.constraints.Range;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.util.Pair;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.bht.saigonparking.api.grpc.user.MapToUsernameMapRequest;
import com.bht.saigonparking.api.grpc.user.UserServiceGrpc;
import com.bht.saigonparking.common.exception.BookingAlreadyFinishedException;
import com.bht.saigonparking.common.exception.BookingAlreadyRatedException;
import com.bht.saigonparking.common.exception.BookingNotYetAcceptedException;
import com.bht.saigonparking.common.exception.BookingNotYetFinishedException;
import com.bht.saigonparking.common.exception.BookingNotYetRatedException;
import com.bht.saigonparking.common.exception.PermissionDeniedException;
import com.bht.saigonparking.service.booking.entity.BookingEntity;
import com.bht.saigonparking.service.booking.entity.BookingHistoryEntity;
import com.bht.saigonparking.service.booking.entity.BookingRatingEntity;
import com.bht.saigonparking.service.booking.entity.BookingStatisticEntity;
import com.bht.saigonparking.service.booking.entity.BookingStatusEntity;
import com.bht.saigonparking.service.booking.mapper.EnumMapper;
import com.bht.saigonparking.service.booking.repository.core.BookingHistoryRepository;
import com.bht.saigonparking.service.booking.repository.core.BookingRatingRepository;
import com.bht.saigonparking.service.booking.repository.core.BookingRepository;
import com.bht.saigonparking.service.booking.repository.core.BookingStatisticRepository;
import com.bht.saigonparking.service.booking.service.main.BookingService;
import com.google.protobuf.Int64Value;

import lombok.RequiredArgsConstructor;

/**
 *
 * @author bht
 */
@Service
@Transactional
@RequiredArgsConstructor(onConstructor = @__(@Autowired))
public class BookingServiceImpl implements BookingService {

    private final EnumMapper enumMapper;
    private final UserServiceGrpc.UserServiceBlockingStub userServiceBlockingStub;

    private final BookingRepository bookingRepository;
    private final BookingRatingRepository bookingRatingRepository;
    private final BookingHistoryRepository bookingHistoryRepository;
    private final BookingStatisticRepository bookingStatisticRepository;

    @Override
    public BookingEntity getOnGoingBookingOfCustomer(@NotNull Long customerId) {
        return bookingRepository.getFirstByCustomerIdAndIsFinished(customerId, Boolean.FALSE).orElseThrow(EntityNotFoundException::new);
    }

    @Override
    public BookingEntity getBookingByUuid(@NotEmpty String uuidString) {
        return bookingRepository.getBookingByUuid(UUID.fromString(uuidString)).orElseThrow(EntityNotFoundException::new);
    }

    @Override
    public BookingEntity getBookingDetailByUuid(@NotEmpty String uuidString) {
        return bookingRepository.getBookingDetailByUuid(UUID.fromString(uuidString)).orElseThrow(EntityNotFoundException::new);
    }

    @Override
    public Pair<String, String> saveNewBooking(@NotNull BookingEntity bookingEntity) {
        BookingEntity newBookingEntity = bookingRepository.saveAndFlush(bookingEntity);
        return Pair.of(newBookingEntity.getUuid().toString(), newBookingEntity.getCreatedAt().toString());
    }

    @Override
    public void saveNewBookingHistory(@NotNull BookingHistoryEntity bookingHistoryEntity, @NotNull String uuidString) {
        BookingEntity bookingEntity = getBookingByUuid(uuidString);
        saveNewBookingHistory(bookingHistoryEntity, bookingEntity);
    }

    private void saveNewBookingHistory(@NotNull BookingHistoryEntity bookingHistoryEntity, @NotNull BookingEntity bookingEntity) {
        if (bookingEntity.getIsFinished().equals(Boolean.FALSE)) {
            bookingHistoryEntity.setBookingEntity(bookingEntity);
            bookingHistoryRepository.saveAndFlush(bookingHistoryEntity);
            return;
        }
        throw new BookingAlreadyFinishedException();
    }

    @Async
    @Override
    public void deleteBookingByUuid(@NotEmpty String uuidString) {
        bookingRepository.delete(getBookingByUuid(uuidString));
    }

    @Override
    public Pair<Long, Long> finishBooking(@NotEmpty String uuidString) {
        BookingEntity bookingEntity = getBookingByUuid(uuidString);

        if (bookingEntity.getBookingStatusEntity().equals(enumMapper.toBookingStatusEntity(CREATED))) {
            throw new BookingNotYetAcceptedException();
        }

        BookingHistoryEntity bookingHistoryEntity = BookingHistoryEntity.builder()
                .bookingStatusEntity(enumMapper.toBookingStatusEntity(FINISHED))
                .version(1L)
                .build();

        saveNewBookingHistory(bookingHistoryEntity, bookingEntity);

        return Pair.of(bookingEntity.getCustomerId(), bookingEntity.getParkingLotId());
    }

    @Override
    public Long countAllBooking() {
        return bookingRepository.countAllBooking();
    }

    @Override
    public Long countAllBooking(@NotNull BookingStatusEntity bookingStatusEntity) {
        return bookingRepository.countAllBooking(bookingStatusEntity);
    }

    @Override
    public Long countAllBookingOfCustomer(@NotNull Long customerId) {
        return bookingRepository.countAllBookingOfCustomer(customerId);
    }

    @Override
    public Long countAllBookingOfParkingLot(@NotNull Long parkingLotId) {
        return bookingRepository.countAllBookingOfParkingLot(parkingLotId);
    }

    @Override
    public Long countAllBookingOfParkingLot(@NotNull Long parkingLotId, @NotNull BookingStatusEntity bookingStatusEntity) {
        return bookingRepository.countAllBookingOfParkingLot(parkingLotId, bookingStatusEntity);
    }

    @Override
    public Long countAllOnGoingBookingOfParkingLot(@NotNull Long parkingLotId) {
        return bookingRepository.countAllOnGoingBookingOfParkingLot(parkingLotId);
    }

    @Override
    public List<BookingEntity> getAllBooking(@NotNull Integer nRow,
                                             @NotNull Integer pageNumber) {

        return bookingRepository.getAllBooking(nRow, pageNumber);
    }

    @Override
    public List<BookingEntity> getAllBooking(@NotNull BookingStatusEntity bookingStatusEntity,
                                             @NotNull Integer nRow,
                                             @NotNull Integer pageNumber) {

        return bookingRepository.getAllBooking(bookingStatusEntity, nRow, pageNumber);
    }

    @Override
    public List<BookingEntity> getAllBookingOfCustomer(@NotNull Long customerId,
                                                       @NotNull Integer nRow,
                                                       @NotNull Integer pageNumber) {

        return bookingRepository.getAllBookingOfCustomer(customerId, nRow, pageNumber);
    }

    @Override
    public List<BookingEntity> getAllBookingOfParkingLot(@NotNull Long parkingLotId,
                                                         @NotNull Integer nRow,
                                                         @NotNull Integer pageNumber) {

        return bookingRepository.getAllBookingOfParkingLot(parkingLotId, nRow, pageNumber);
    }

    @Override
    public List<BookingEntity> getAllBookingOfParkingLot(@NotNull Long parkingLotId,
                                                         @NotNull BookingStatusEntity bookingStatusEntity,
                                                         @NotNull Integer nRow,
                                                         @NotNull Integer pageNumber) {

        return bookingRepository.getAllBookingOfParkingLot(parkingLotId, bookingStatusEntity, nRow, pageNumber);
    }

    @Override
    public List<BookingEntity> getAllOnGoingBookingOfParkingLot(@NotNull Long parkingLotId) {
        return bookingRepository.getAllOnGoingBookingOfParkingLot(parkingLotId);
    }

    @Override
    public Map<Long, Long> countAllBookingGroupByStatus() {
        return bookingRepository.countAllBookingGroupByStatus().stream().collect(Collectors
                .toMap(tuple -> enumMapper.toBookingStatusValue(tuple.get(0, Long.class)), tuple -> tuple.get(1, Long.class)));
    }

    @Override
    public Map<Long, Long> countAllBookingOfParkingLotGroupByStatus(@NotNull Long parkingLotId) {
        return bookingRepository.countAllBookingOfParkingLotGroupByStatus(parkingLotId).stream().collect(Collectors
                .toMap(tuple -> enumMapper.toBookingStatusValue(tuple.get(0, Long.class)), tuple -> tuple.get(1, Long.class)));
    }

    @Override
    public boolean checkCustomerHasOnGoingBooking(@NotNull Long customerId) {
        return bookingRepository.countAllUnfinishedBookingByCustomerId(customerId) != 0;
    }

    @Override
    public Long countAllRatingsOfParkingLot(@NotNull Long parkingLotId) {
        return bookingRatingRepository.countAllRatingsOfParkingLot(parkingLotId);
    }

    @Override
    public Long countAllRatingsOfParkingLot(@NotNull Long parkingLotId,
                                            @NotNull @Range(max = 5L) Integer rating) {

        if (rating.equals(0)) {
            return countAllRatingsOfParkingLot(parkingLotId);
        }
        return bookingRatingRepository.countAllRatingsOfParkingLot(parkingLotId, rating);
    }

    @Override
    public Map<Tuple, String> getAllRatingsOfParkingLot(@NotNull Long parkingLotId,
                                                        boolean sortLastUpdatedAsc,
                                                        @NotNull @Max(20L) Integer nRow,
                                                        @NotNull Integer pageNumber) {

        List<Tuple> parkingLotRatingTupleList = bookingRatingRepository
                .getAllRatingsOfParkingLot(parkingLotId, sortLastUpdatedAsc, nRow, pageNumber);

        Map<Long, String> usernameMap = userServiceBlockingStub.mapToUsernameMap(MapToUsernameMapRequest.newBuilder()
                .addAllUserId(parkingLotRatingTupleList.stream()
                        .map(tuple -> tuple.get(2, Long.class)).collect(Collectors.toSet()))
                .build())
                .getUsernameMap();

        return parkingLotRatingTupleList.stream().collect(Collectors
                .toMap(parkingLotRatingTuple -> parkingLotRatingTuple,
                        parkingLotRatingTuple -> usernameMap.get(parkingLotRatingTuple.get(2, Long.class))));
    }

    @Override
    public Map<Tuple, String> getAllRatingsOfParkingLot(@NotNull Long parkingLotId,
                                                        @NotNull @Range(max = 5L) Integer rating,
                                                        boolean sortLastUpdatedAsc,
                                                        @NotNull @Max(20L) Integer nRow,
                                                        @NotNull Integer pageNumber) {

        if (!rating.equals(0)) {
            List<Tuple> parkingLotRatingTupleList = bookingRatingRepository
                    .getAllRatingsOfParkingLot(parkingLotId, rating, sortLastUpdatedAsc, nRow, pageNumber);

            Map<Long, String> usernameMap = userServiceBlockingStub.mapToUsernameMap(MapToUsernameMapRequest.newBuilder()
                    .addAllUserId(parkingLotRatingTupleList.stream()
                            .map(tuple -> tuple.get(2, Long.class)).collect(Collectors.toSet()))
                    .build())
                    .getUsernameMap();

            return parkingLotRatingTupleList.stream().collect(Collectors
                    .toMap(parkingLotRatingTuple -> parkingLotRatingTuple,
                            parkingLotRatingTuple -> usernameMap.get(parkingLotRatingTuple.get(2, Long.class))));
        }

        return getAllRatingsOfParkingLot(parkingLotId, sortLastUpdatedAsc, nRow, pageNumber);
    }

    @Override
    public Map<Integer, Long> getParkingLotRatingCountGroupByRating(@NotNull Long parkingLotId) {
        return bookingRatingRepository.getParkingLotRatingCountGroupByRating(parkingLotId);
    }

    @Override
    public Long createBookingRating(@NotNull Long customerId,
                                    @NotNull String bookingUuidString,
                                    @NotNull Integer rating,
                                    @NotEmpty String comment) {

        BookingEntity bookingEntity = getBookingByUuid(bookingUuidString);
        if (customerId.equals(bookingEntity.getCustomerId())) {
            if (Boolean.TRUE.equals(bookingEntity.getIsFinished())) {
                BookingRatingEntity currentBookingRating = bookingEntity.getBookingRatingEntity();

                if (currentBookingRating == null) {
                    BookingRatingEntity bookingRatingEntity = BookingRatingEntity.builder()
                            .bookingEntity(bookingEntity)
                            .rating(rating.shortValue())
                            .comment(comment)
                            .build();
                    return bookingRatingRepository.saveAndFlush(bookingRatingEntity).getId();
                }
                throw new BookingAlreadyRatedException();
            }
            throw new BookingNotYetFinishedException();
        }
        throw new PermissionDeniedException();
    }

    @Override
    public void updateBookingRating(@NotNull Long customerId,
                                    @NotNull String bookingUuidString,
                                    @NotNull Integer rating,
                                    @NotEmpty String comment) {

        BookingEntity bookingEntity = getBookingByUuid(bookingUuidString);
        if (customerId.equals(bookingEntity.getCustomerId())) {
            BookingRatingEntity currentBookingRating = bookingEntity.getBookingRatingEntity();

            if (currentBookingRating != null) {
                currentBookingRating.setRating(rating.shortValue());
                currentBookingRating.setComment(comment);
                bookingRatingRepository.saveAndFlush(currentBookingRating);
                return;
            }
            throw new BookingNotYetRatedException();
        }
        throw new PermissionDeniedException();
    }

    @Override
    public void deleteBookingRating(@NotNull Long customerId, @NotEmpty String bookingUuidString) {

        BookingEntity bookingEntity = getBookingByUuid(bookingUuidString);
        if (customerId.equals(bookingEntity.getCustomerId())) {
            BookingRatingEntity currentBookingRating = bookingEntity.getBookingRatingEntity();
            if (currentBookingRating != null) {
                bookingEntity.setBookingRatingEntity(null);
                bookingRatingRepository.delete(currentBookingRating);
                return;
            }
            throw new BookingNotYetRatedException();
        }
        throw new PermissionDeniedException();
    }

    @Override
    public Pair<BookingRatingEntity, String> getBookingRatingWithCustomerUsernameByBookingUuid(@NotEmpty String bookingUuidString) {
        BookingRatingEntity ratingEntity = getBookingRatingByBookingUuid(bookingUuidString);
        String customerUsername = userServiceBlockingStub
                .mapUserIdToUsername(Int64Value.of(ratingEntity.getBookingEntity().getCustomerId()))
                .getValue();

        return Pair.of(ratingEntity, customerUsername);
    }

    private BookingRatingEntity getBookingRatingByBookingUuid(@NotEmpty String bookingUuidString) {
        return bookingRatingRepository.getByBookingUuid(UUID.fromString(bookingUuidString)).orElseThrow(EntityNotFoundException::new);
    }

    @Async
    @Override
    public void createOneOrManyParkingLotStatistic(@NotNull Set<Long> parkingLotIdSet) {
        parkingLotIdSet.forEach(this::createParkingLotStatistic);
    }

    @Async
    @Override
    public void deleteOneOrManyParkingLotStatistic(@NotNull Set<Long> parkingLotIdSet) {
        parkingLotIdSet.forEach(this::deleteParkingLotStatistic);
    }

    private void createParkingLotStatistic(@NotNull Long parkingLotId) {
        Optional<BookingStatisticEntity> currentStatistic = bookingStatisticRepository.getByParkingLotId(parkingLotId);

        if (!currentStatistic.isPresent()) {
            bookingStatisticRepository.saveAndFlush(BookingStatisticEntity.builder()
                    .parkingLotId(parkingLotId)
                    .nBooking(0L)
                    .nRating(0L)
                    .ratingAverage((double) 0)
                    .build());
        }
    }

    private void deleteParkingLotStatistic(@NotNull Long parkingLotId) {
        bookingStatisticRepository.getByParkingLotId(parkingLotId).ifPresent(bookingStatisticRepository::delete);
    }

    @Override
    public BookingStatisticEntity getParkingLotBookingAndRatingStatistic(@NotNull Long parkingLotId) {
        return bookingStatisticRepository.getByParkingLotId(parkingLotId).orElseThrow(EntityNotFoundException::new);
    }
}

// Node: repos/cloned_ms_repos/saigonparking/service/booking-service/src/main/java/com/bht/saigonparking/service/booking/service/main/impl/BookingServiceImpl.java:BookingServiceImpl.<init>
package com.bht.saigonparking.service.mail.configuration;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.stereotype.Component;

/**
 *
 * @author bht
 */
@Component
public final class MailConfiguration {

    @Value("${saigonparking.domain}")
    private String saigonParkingDomain;

    @Bean("activateAccountEmailTemplate")
    public String activateAccountEmailTemplate() {
        return "<p> " +
                "Welcome to Saigon Parking, <b><i>%s</i></b>,<br/>" +
                "<br/>" +
                "Please click the link below to activate your account:<br/><br/>" +
                "<a href=\"" + saigonParkingDomain + "/activate-account?token=%s" + "\">" +
                "Activate account link" +
                "</a><br/>" +
                "<br/>" +
                "Please notice that the link we provide above will be expired in 5 minutes !<br/>" +
                "Please do not reply this email as this is an auto-generated email !<br/><br/>" +
                "Yours sincerely, Saigon Parking VN. " +
                "</p>";
    }

    @Bean("resetPasswordEmailTemplate")
    public String resetPasswordEmailTemplate() {
        return "<p> " +
                "Dear <b><i>%s</i></b>,<br/>" +
                "<br/>" +
                "Please click the link below to reset your account password:<br/><br/>" +
                "<a href=\"" + saigonParkingDomain + "/reset-password?token=%s" + "\">" +
                "Reset password link" +
                "</a><br/>" +
                "<br/>" +
                "Please notice that the link we provide above will be expired in 5 minutes !<br/>" +
                "Please do not reply this email as this is an auto-generated email !<br/><br/>" +
                "Yours sincerely, Saigon Parking VN. " +
                "</p>";
    }
}

// Node: repos/cloned_ms_repos/saigonparking/service/mail-service/src/main/java/com/bht/saigonparking/service/mail/configuration/MailConfiguration.java:MailConfiguration.<init>
// Node: activateAccountEmailTemplate
package com.bht.saigonparking.service.mail.configuration;

import static com.bht.saigonparking.common.constant.SaigonParkingMessageQueue.MAIL_QUEUE_NAME;

import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;

import com.bht.saigonparking.api.grpc.mail.MailRequest;
import com.bht.saigonparking.service.mail.service.MailService;

import lombok.AllArgsConstructor;

/**
 *
 * @author bht
 */
@Component
@AllArgsConstructor(onConstructor = @__(@Autowired))
public class MessageQueueConfiguration {

    private final MailService mailService;

    @Async
    @RabbitListener(queues = {MAIL_QUEUE_NAME})
    public void consumeMessageFromMailTopic(MailRequest request) {
        mailService.sendNewMail(request);
    }
}

// Node: repos/cloned_ms_repos/saigonparking/service/mail-service/src/main/java/com/bht/saigonparking/service/mail/configuration/MessageQueueConfiguration.java:MessageQueueConfiguration.<init>
package com.bht.saigonparking.service.mail.service;

import javax.mail.internet.MimeMessage;

import org.apache.logging.log4j.Level;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import com.bht.saigonparking.api.grpc.mail.MailRequest;
import com.bht.saigonparking.api.grpc.mail.MailRequestType;
import com.bht.saigonparking.common.util.LoggingUtil;

import lombok.RequiredArgsConstructor;

/**
 *
 * @author bht
 */
@Service
@RequiredArgsConstructor(onConstructor = @__(@Autowired))
public class MailServiceImpl implements MailService {

    private final JavaMailSender mailSender;

    @Qualifier("activateAccountEmailTemplate")
    private final String activateAccountEmailTemplate;

    @Qualifier("resetPasswordEmailTemplate")
    private final String resetPasswordEmailTemplate;

    @Async
    @Override
    public void sendNewMail(MailRequest request) {
        boolean isActivateEmail = request.getType().equals(MailRequestType.ACTIVATE_ACCOUNT);
        try {
            MimeMessage message = mailSender.createMimeMessage();
            MimeMessageHelper messageHelper = new MimeMessageHelper(message, "utf-8");

            String subject = isActivateEmail
                    ? "[Saigon Parking] Activate new account"
                    : "[Saigon Parking] Reset password";

            String htmlContent = isActivateEmail
                    ? String.format(activateAccountEmailTemplate, request.getUsername(), request.getTemporaryToken())
                    : String.format(resetPasswordEmailTemplate, request.getUsername(), request.getTemporaryToken());

            messageHelper.setTo(request.getEmail());
            messageHelper.setSubject(subject);
            messageHelper.setText(htmlContent, true);
            mailSender.send(messageHelper.getMimeMessage());

            LoggingUtil.log(Level.INFO, "SERVICE", "Success", "send"
                    + (isActivateEmail ? "ActivateAccount" : "ResetPassword")
                    + "EmailToUser(" + request.getUsername() + ")");

        } catch (Exception exception) {

            LoggingUtil.log(Level.WARN, "SERVICE", "Fail", "send"
                    + (isActivateEmail ? "ActivateAccount" : "ResetPassword")
                    + "EmailToUser(" + request.getUsername() + "): "
                    + exception.getMessage());
        }
    }
}

// Node: repos/cloned_ms_repos/saigonparking/service/mail-service/src/main/java/com/bht/saigonparking/service/mail/service/MailServiceImpl.java:MailServiceImpl.<init>
package com.bht.saigonparking.service.contact.interceptor.main;

import java.util.List;
import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.server.ServerHttpRequest;
import org.springframework.lang.NonNull;
import org.springframework.stereotype.Component;

import com.bht.saigonparking.common.auth.SaigonParkingAuthentication;
import com.bht.saigonparking.common.auth.SaigonParkingTokenBody;
import com.bht.saigonparking.common.base.BaseWebSocketHandshakeInterceptor;
import com.bht.saigonparking.common.exception.MissingTokenException;
import com.bht.saigonparking.service.contact.service.HandshakeService;

import lombok.RequiredArgsConstructor;

/**
 *
 * @author bht
 */
@Component
@RequiredArgsConstructor(onConstructor = @__(@Autowired))
public final class WebSocketHandshakeInterceptor extends BaseWebSocketHandshakeInterceptor {

    private static final String USER_AUTHORIZATION_KEY = "Authorization";
    private static final boolean MUST_CONSUME_MESSAGE_FROM_QUEUE = true;

    private final HandshakeService handshakeService;
    private final SaigonParkingAuthentication saigonParkingAuthentication;

    @Override
    protected SaigonParkingAuthentication getAuthentication() {
        return saigonParkingAuthentication;
    }

    @Override
    protected String getAccessTokenFromHttpRequest(@NonNull ServerHttpRequest httpRequest) {
        List<String> authorizationHeaders = httpRequest.getHeaders().get(USER_AUTHORIZATION_KEY);
        if (authorizationHeaders == null || authorizationHeaders.isEmpty()) {
            throw new MissingTokenException();
        }
        return authorizationHeaders.get(0);
    }

    @Override
    protected void postAuthentication(@NonNull SaigonParkingTokenBody saigonParkingTokenBody,
                                      @NonNull Map<String, Object> webSocketSessionAttributes) {

        webSocketSessionAttributes.putAll(handshakeService.postAuthentication(saigonParkingTokenBody, MUST_CONSUME_MESSAGE_FROM_QUEUE));
    }
}

// Node: repos/cloned_ms_repos/saigonparking/service/contact-service/src/main/java/com/bht/saigonparking/service/contact/interceptor/main/WebSocketHandshakeInterceptor.java:WebSocketHandshakeInterceptor.<init>
package com.bht.saigonparking.service.contact.interceptor.main;

import static com.bht.saigonparking.service.contact.configuration.WebSocketConfiguration.WEB_AUTH_PATH_PREFIX;
import static com.bht.saigonparking.service.contact.configuration.WebSocketConfiguration.WEB_AUTH_PATH_PREFIX_LENGTH;

import java.net.URI;
import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.server.ServerHttpRequest;
import org.springframework.lang.NonNull;
import org.springframework.stereotype.Component;

import com.bht.saigonparking.common.auth.SaigonParkingAuthentication;
import com.bht.saigonparking.common.auth.SaigonParkingTokenBody;
import com.bht.saigonparking.common.base.BaseWebSocketHandshakeInterceptor;
import com.bht.saigonparking.common.exception.MissingTokenException;
import com.bht.saigonparking.service.contact.service.HandshakeService;

import lombok.RequiredArgsConstructor;

/**
 *
 * @author bht
 */
@Component
@RequiredArgsConstructor(onConstructor = @__(@Autowired))
public final class WebSocketHandshakeWebInterceptor extends BaseWebSocketHandshakeInterceptor {

    private static final boolean MUST_CONSUME_MESSAGE_FROM_QUEUE = true;

    private final SaigonParkingAuthentication authentication;
    private final HandshakeService handshakeService;

    @Override
    protected SaigonParkingAuthentication getAuthentication() {
        return authentication;
    }

    @Override
    protected String getAccessTokenFromHttpRequest(@NonNull ServerHttpRequest httpRequest) {
        String accessToken = getAccessTokenFromUri(httpRequest.getURI());
        if (accessToken.isEmpty()) {
            throw new MissingTokenException();
        }
        return accessToken;
    }

    @Override
    protected void postAuthentication(@NonNull SaigonParkingTokenBody saigonParkingTokenBody,
                                      @NonNull Map<String, Object> webSocketSessionAttributes) {

        webSocketSessionAttributes.putAll(handshakeService.postAuthentication(saigonParkingTokenBody, MUST_CONSUME_MESSAGE_FROM_QUEUE));
    }

    private String getAccessTokenFromUri(@NonNull URI uriWithAccessToken) {
        String uriString = uriWithAccessToken.toString();
        return uriString.substring(uriString.lastIndexOf(WEB_AUTH_PATH_PREFIX) + WEB_AUTH_PATH_PREFIX_LENGTH);
    }
}

// Node: repos/cloned_ms_repos/saigonparking/service/contact-service/src/main/java/com/bht/saigonparking/service/contact/interceptor/main/WebSocketHandshakeWebInterceptor.java:WebSocketHandshakeWebInterceptor.<init>
package com.bht.saigonparking.service.contact.interceptor.auxiliary;

import static com.bht.saigonparking.service.contact.configuration.WebSocketConfiguration.WEB_AUTH_PATH_PREFIX;
import static com.bht.saigonparking.service.contact.configuration.WebSocketConfiguration.WEB_AUTH_PATH_PREFIX_LENGTH;

import java.net.URI;
import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.server.ServerHttpRequest;
import org.springframework.lang.NonNull;
import org.springframework.stereotype.Component;

import com.bht.saigonparking.common.auth.SaigonParkingAuthentication;
import com.bht.saigonparking.common.auth.SaigonParkingTokenBody;
import com.bht.saigonparking.common.base.BaseWebSocketHandshakeInterceptor;
import com.bht.saigonparking.common.exception.MissingTokenException;
import com.bht.saigonparking.service.contact.service.HandshakeService;

import lombok.RequiredArgsConstructor;

/**
 *
 * @author bht
 */
@Component
@RequiredArgsConstructor(onConstructor = @__(@Autowired))
public final class WebSocketHandshakeQrScannerWebInterceptor extends BaseWebSocketHandshakeInterceptor {

    private static final boolean MUST_CONSUME_MESSAGE_FROM_QUEUE = false;

    private final SaigonParkingAuthentication authentication;
    private final HandshakeService handshakeService;

    @Override
    protected SaigonParkingAuthentication getAuthentication() {
        return authentication;
    }

    @Override
    protected String getAccessTokenFromHttpRequest(@NonNull ServerHttpRequest httpRequest) {
        String accessToken = getAccessTokenFromUri(httpRequest.getURI());
        if (accessToken.isEmpty()) {
            throw new MissingTokenException();
        }
        return accessToken;
    }

    @Override
    protected void postAuthentication(@NonNull SaigonParkingTokenBody saigonParkingTokenBody,
                                      @NonNull Map<String, Object> webSocketSessionAttributes) {

        webSocketSessionAttributes.putAll(handshakeService.postAuthentication(saigonParkingTokenBody, MUST_CONSUME_MESSAGE_FROM_QUEUE));
    }

    private String getAccessTokenFromUri(@NonNull URI uriWithAccessToken) {
        String uriString = uriWithAccessToken.toString();
        return uriString.substring(uriString.lastIndexOf(WEB_AUTH_PATH_PREFIX) + WEB_AUTH_PATH_PREFIX_LENGTH);
    }
}

// Node: repos/cloned_ms_repos/saigonparking/service/contact-service/src/main/java/com/bht/saigonparking/service/contact/interceptor/auxiliary/WebSocketHandshakeQrScannerWebInterceptor.java:WebSocketHandshakeQrScannerWebInterceptor.<init>
package com.bht.saigonparking.service.contact.interceptor.auxiliary;

import java.util.List;
import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.server.ServerHttpRequest;
import org.springframework.lang.NonNull;
import org.springframework.stereotype.Component;

import com.bht.saigonparking.common.auth.SaigonParkingAuthentication;
import com.bht.saigonparking.common.auth.SaigonParkingTokenBody;
import com.bht.saigonparking.common.base.BaseWebSocketHandshakeInterceptor;
import com.bht.saigonparking.common.exception.MissingTokenException;
import com.bht.saigonparking.service.contact.service.HandshakeService;

import lombok.RequiredArgsConstructor;

/**
 *
 * @author bht
 */
@Component
@RequiredArgsConstructor(onConstructor = @__(@Autowired))
public final class WebSocketHandshakeQrScannerInterceptor extends BaseWebSocketHandshakeInterceptor {

    private static final String USER_AUTHORIZATION_KEY = "Authorization";
    private static final boolean MUST_CONSUME_MESSAGE_FROM_QUEUE = false;

    private final SaigonParkingAuthentication authentication;
    private final HandshakeService handshakeService;

    @Override
    protected SaigonParkingAuthentication getAuthentication() {
        return authentication;
    }

    @Override
    protected String getAccessTokenFromHttpRequest(@NonNull ServerHttpRequest httpRequest) {
        List<String> authorizationHeaders = httpRequest.getHeaders().get(USER_AUTHORIZATION_KEY);
        if (authorizationHeaders == null || authorizationHeaders.isEmpty()) {
            throw new MissingTokenException();
        }
        return authorizationHeaders.get(0);
    }

    @Override
    protected void postAuthentication(@NonNull SaigonParkingTokenBody saigonParkingTokenBody,
                                      @NonNull Map<String, Object> webSocketSessionAttributes) {

        webSocketSessionAttributes.putAll(handshakeService.postAuthentication(saigonParkingTokenBody, MUST_CONSUME_MESSAGE_FROM_QUEUE));
    }
}

// Node: repos/cloned_ms_repos/saigonparking/service/contact-service/src/main/java/com/bht/saigonparking/service/contact/interceptor/auxiliary/WebSocketHandshakeQrScannerInterceptor.java:WebSocketHandshakeQrScannerInterceptor.<init>
package com.bht.saigonparking.service.contact.configuration;

import java.util.concurrent.TimeUnit;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.client.discovery.DiscoveryClient;
import org.springframework.context.annotation.Bean;
import org.springframework.stereotype.Component;

import com.bht.saigonparking.api.grpc.booking.BookingServiceGrpc;
import com.bht.saigonparking.api.grpc.parkinglot.ParkingLotServiceGrpc;
import com.bht.saigonparking.common.interceptor.SaigonParkingClientInterceptor;
import com.bht.saigonparking.common.loadbalance.SaigonParkingNameResolverProvider;

import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import lombok.AllArgsConstructor;

/**
 *
 * @author bht
 */
@Component
@AllArgsConstructor(onConstructor = @__(@Autowired))
public final class ChannelConfiguration {

    private final SaigonParkingClientInterceptor clientInterceptor;

    @Bean("parkingLotResolver")
    public SaigonParkingNameResolverProvider userServiceNameResolver(@Value("${connection.parkinglot-service.id}") String serviceId,
                                                                     @Autowired DiscoveryClient discoveryClient) {

        return new SaigonParkingNameResolverProvider(serviceId, discoveryClient);
    }

    @Bean("bookingResolver")
    public SaigonParkingNameResolverProvider bookingServiceNameResolver(@Value("${connection.booking-service.id}") String serviceId,
                                                                        @Autowired DiscoveryClient discoveryClient) {
        
        return new SaigonParkingNameResolverProvider(serviceId, discoveryClient);
    }

    /**
     *
     * channel is the abstraction to connect to a service endpoint
     *
     * note for gRPC service stub:
     *      .newStub(channel)          --> nonblocking/asynchronous stub
     *      .newBlockingStub(channel)  --> blocking/synchronous stub
     */
    @Bean("parkingLotChannel")
    public ManagedChannel parkingLotChannel(@Value("${spring.cloud.consul.host}") String host,
                                            @Value("${spring.cloud.consul.port}") int port,
                                            @Value("${connection.idle-timeout}") int timeout,
                                            @Value("${connection.max-inbound-message-size}") int maxInBoundMessageSize,
                                            @Value("${connection.max-inbound-metadata-size}") int maxInBoundMetadataSize,
                                            @Value("${connection.load-balancing-policy}") String loadBalancingPolicy,
                                            @Qualifier("parkingLotResolver") SaigonParkingNameResolverProvider nameResolverProvider) {

        return ManagedChannelBuilder
                .forTarget("consul://" + host + ":" + port)                     // build channel to server with server's address
                .keepAliveWithoutCalls(false)                                   // Close channel when client has already received response
                .idleTimeout(timeout, TimeUnit.MILLISECONDS)                    // 10000 milliseconds / 1000 = 10 seconds --> request time-out
                .maxInboundMetadataSize(maxInBoundMetadataSize * 1024 * 1024)   // 2KB * 1024 = 2MB --> max message header size
                .maxInboundMessageSize(maxInBoundMessageSize * 1024 * 1024)     // 10KB * 1024 = 10MB --> max message size to transfer together
                .defaultLoadBalancingPolicy(loadBalancingPolicy)                // set load balancing policy for channel
                .nameResolverFactory(nameResolverProvider)                      // using Consul service discovery for DNS querying
                .intercept(clientInterceptor)                                   // add internal credential authentication
                .usePlaintext()                                                 // use plain-text to communicate internally
                .build();                                                       // Build channel to communicate over gRPC
    }

    @Bean("bookingChannel")
    public ManagedChannel bookingChannel(@Value("${spring.cloud.consul.host}") String host,
                                         @Value("${spring.cloud.consul.port}") int port,
                                         @Value("${connection.idle-timeout}") int timeout,
                                         @Value("${connection.max-inbound-message-size}") int maxInBoundMessageSize,
                                         @Value("${connection.max-inbound-metadata-size}") int maxInBoundMetadataSize,
                                         @Value("${connection.load-balancing-policy}") String loadBalancingPolicy,
                                         @Qualifier("bookingResolver") SaigonParkingNameResolverProvider nameResolverProvider) {

        return ManagedChannelBuilder
                .forTarget("consul://" + host + ":" + port)                     // build channel to server with server's address
                .keepAliveWithoutCalls(false)                                   // Close channel when client has already received response
                .idleTimeout(timeout, TimeUnit.MILLISECONDS)                    // 10000 milliseconds / 1000 = 10 seconds --> request time-out
                .maxInboundMetadataSize(maxInBoundMetadataSize * 1024 * 1024)   // 2KB * 1024 = 2MB --> max message header size
                .maxInboundMessageSize(maxInBoundMessageSize * 1024 * 1024)     // 10KB * 1024 = 10MB --> max message size to transfer together
                .defaultLoadBalancingPolicy(loadBalancingPolicy)                // set load balancing policy for channel
                .nameResolverFactory(nameResolverProvider)                      // using Consul service discovery for DNS querying
                .intercept(clientInterceptor)                                   // add internal credential authentication
                .usePlaintext()                                                 // use plain-text to communicate internally
                .build();                                                       // Build channel to communicate over gRPC
    }

    /* asynchronous parking-lot service stub */
    @Bean
    public ParkingLotServiceGrpc.ParkingLotServiceStub parkingLotServiceStub(@Qualifier("parkingLotChannel") ManagedChannel channel) {
        return ParkingLotServiceGrpc.newStub(channel);
    }

    /* synchronous parking-lot service stub */
    @Bean
    public ParkingLotServiceGrpc.ParkingLotServiceBlockingStub parkingLotServiceBlockingStub(@Qualifier("parkingLotChannel") ManagedChannel channel) {
        return ParkingLotServiceGrpc.newBlockingStub(channel);
    }

    /* asynchronous booking service stub */
    @Bean
    public BookingServiceGrpc.BookingServiceStub bookingServiceStub(@Qualifier("bookingChannel") ManagedChannel channel) {
        return BookingServiceGrpc.newStub(channel);
    }

    /* synchronous booking service stub */
    @Bean
    public BookingServiceGrpc.BookingServiceBlockingStub bookingServiceBlockingStub(@Qualifier("bookingChannel") ManagedChannel channel) {
        return BookingServiceGrpc.newBlockingStub(channel);
    }
}

// Node: repos/cloned_ms_repos/saigonparking/service/contact-service/src/main/java/com/bht/saigonparking/service/contact/configuration/ChannelConfiguration.java:ChannelConfiguration.<init>
// Node: bookingServiceNameResolver
// Node: bookingChannel
// Node: bookingServiceStub
// Node: bookingServiceBlockingStub
package com.bht.saigonparking.service.contact.configuration;

import static com.bht.saigonparking.common.constant.SaigonParkingMessageQueue.CONTACT_EXCHANGE_NAME;

import org.springframework.amqp.core.AcknowledgeMode;
import org.springframework.amqp.core.TopicExchange;
import org.springframework.amqp.rabbit.connection.ConnectionFactory;
import org.springframework.amqp.rabbit.listener.AbstractMessageListenerContainer;
import org.springframework.amqp.rabbit.listener.DirectMessageListenerContainer;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.stereotype.Component;

import com.bht.saigonparking.service.contact.listener.SaigonParkingQueueMessageListener;

import lombok.RequiredArgsConstructor;

/**
 *
 * @author bht
 */
@Component
@RequiredArgsConstructor(onConstructor = @__(@Autowired))
public final class MessageQueueConfiguration {

    private final ConnectionFactory connectionFactory;
    private final SaigonParkingQueueMessageListener saigonParkingQueueMessageListener;

    @Bean
    public TopicExchange topicExchange() {
        return new TopicExchange(CONTACT_EXCHANGE_NAME);
    }

    @Bean
    public AbstractMessageListenerContainer simpleMessageListenerContainer() {
        DirectMessageListenerContainer container = new DirectMessageListenerContainer();
        container.setMessageListener(saigonParkingQueueMessageListener);
        container.setConnectionFactory(connectionFactory);
        container.setAcknowledgeMode(AcknowledgeMode.AUTO);
        return container;
    }
}

// Node: repos/cloned_ms_repos/saigonparking/service/contact-service/src/main/java/com/bht/saigonparking/service/contact/configuration/MessageQueueConfiguration.java:MessageQueueConfiguration.<init>
package com.bht.saigonparking.service.contact.service;

import java.io.IOException;

import javax.validation.constraints.NotNull;

import com.google.zxing.WriterException;

/**
 *
 * @author bht
 */
public interface QrCodeService {

    byte[] encodeContents(@NotNull String contents) throws WriterException, IOException;
}

// Node: repos/cloned_ms_repos/saigonparking/service/contact-service/src/main/java/com/bht/saigonparking/service/contact/service/QrCodeService.java:QrCodeService.<init>
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

// Node: repos/cloned_ms_repos/saigonparking/service/contact-service/src/main/java/com/bht/saigonparking/service/contact/service/grpc/ContactServiceGrpcImpl.java:ContactServiceGrpcImpl.<init>
package com.bht.saigonparking.service.contact.service.impl;

import java.io.ByteArrayOutputStream;
import java.io.IOException;

import javax.validation.constraints.NotNull;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import com.bht.saigonparking.service.contact.service.QrCodeService;
import com.google.protobuf.Internal;
import com.google.zxing.BarcodeFormat;
import com.google.zxing.WriterException;
import com.google.zxing.client.j2se.MatrixToImageWriter;
import com.google.zxing.common.BitMatrix;
import com.google.zxing.qrcode.QRCodeWriter;

import lombok.RequiredArgsConstructor;

/**
 *
 * @author bht
 */
@Service
@RequiredArgsConstructor(onConstructor = @__(@Autowired))
public final class QrCodeServiceImpl implements QrCodeService {

    private final QRCodeWriter qrCodeWriter;

    @Value("${qr-code.width}")
    private Integer qrCodeWidth;

    @Value("${qr-code.height}")
    private Integer qrCodeHeight;

    @Override
    public byte[] encodeContents(@NotNull String contents) throws WriterException, IOException {
        if (!contents.isEmpty()) {
            ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream();
            BitMatrix bitMatrix = qrCodeWriter.encode(contents, BarcodeFormat.QR_CODE, qrCodeWidth, qrCodeHeight);
            MatrixToImageWriter.writeToStream(bitMatrix, "PNG", byteArrayOutputStream);
            return byteArrayOutputStream.toByteArray();
        }
        return Internal.EMPTY_BYTE_ARRAY;
    }
}

// Node: repos/cloned_ms_repos/saigonparking/service/contact-service/src/main/java/com/bht/saigonparking/service/contact/service/impl/QrCodeServiceImpl.java:QrCodeServiceImpl.<init>
package com.bht.saigonparking.service.contact.service.impl;

import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;

import org.springframework.amqp.core.AmqpAdmin;
import org.springframework.amqp.core.BindingBuilder;
import org.springframework.amqp.core.FanoutExchange;
import org.springframework.amqp.core.Queue;
import org.springframework.amqp.core.TopicExchange;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.amqp.rabbit.listener.AbstractMessageListenerContainer;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.bht.saigonparking.common.constant.SaigonParkingMessageQueue;
import com.bht.saigonparking.service.contact.service.QueueService;

import lombok.RequiredArgsConstructor;

/**
 *
 * @author bht
 */
@Service
@RequiredArgsConstructor(onConstructor = @__(@Autowired))
public final class QueueServiceImpl implements QueueService {

    private final AmqpAdmin amqpAdmin;
    private final RabbitTemplate rabbitTemplate;
    private final TopicExchange contactTopicExchange;
    private final AbstractMessageListenerContainer messageListenerContainer;

    @Override
    public Queue registerAutoDeleteQueueForUser(@NotNull Long userId) {

        String queueName = SaigonParkingMessageQueue.getUserQueueName(userId);
        String routingKey = SaigonParkingMessageQueue.generateUserRoutingKey(userId);
        Queue autoDeleteUserQueue = new Queue(queueName, false, false, true);

        amqpAdmin.declareQueue(autoDeleteUserQueue);
        amqpAdmin.declareBinding(BindingBuilder.bind(autoDeleteUserQueue).to(contactTopicExchange).with(routingKey));
        messageListenerContainer.addQueues(autoDeleteUserQueue);

        return autoDeleteUserQueue;
    }

    @Override
    public void registerAutoDeleteExchangeForParkingLot(@NotNull Long parkingLotId, @NotNull Queue employeeQueue) {

        String exchangeName = SaigonParkingMessageQueue.getParkingLotExchangeName(parkingLotId);
        FanoutExchange parkingLotExchange = new FanoutExchange(exchangeName, false, true);

        amqpAdmin.declareExchange(parkingLotExchange);
        amqpAdmin.declareBinding(BindingBuilder.bind(employeeQueue).to(parkingLotExchange));
    }

    @Override
    public boolean isExchangeExist(@NotEmpty String exchangeName) {
        return rabbitTemplate.execute(channel -> {
            try {
                return channel.exchangeDeclarePassive(exchangeName);

            } catch (Exception exception) {
                return null;
            }
        }) != null;
    }

    @Override
    public boolean isQueueExist(@NotEmpty String queueName) {
        return rabbitTemplate.execute(channel -> {
            try {
                return channel.queueDeclarePassive(queueName);

            } catch (Exception exception) {
                return null;
            }
        }) != null;
    }
}

// Node: repos/cloned_ms_repos/saigonparking/service/contact-service/src/main/java/com/bht/saigonparking/service/contact/service/impl/QueueServiceImpl.java:QueueServiceImpl.<init>
package com.bht.saigonparking.service.contact.service.impl;

import javax.validation.constraints.NotNull;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.bht.saigonparking.common.constant.SaigonParkingMessageQueue;
import com.bht.saigonparking.service.contact.service.ConnectivityService;
import com.bht.saigonparking.service.contact.service.QueueService;

import lombok.RequiredArgsConstructor;

/**
 *
 * @author bht
 */
@Service
@RequiredArgsConstructor(onConstructor = @__(@Autowired))
public final class ConnectivityServiceImpl implements ConnectivityService {

    private final QueueService queueService;

    @Override
    public boolean isUserOnline(@NotNull Long userId) {
        return queueService.isQueueExist(SaigonParkingMessageQueue.getUserQueueName(userId));
    }

    @Override
    public boolean isParkingLotOnline(@NotNull Long parkingLotId) {
        return queueService.isExchangeExist(SaigonParkingMessageQueue.getParkingLotExchangeName(parkingLotId));
    }
}

// Node: repos/cloned_ms_repos/saigonparking/service/contact-service/src/main/java/com/bht/saigonparking/service/contact/service/impl/ConnectivityServiceImpl.java:ConnectivityServiceImpl.<init>
package com.bht.saigonparking.service.contact.listener;

import javax.validation.constraints.NotNull;

import org.springframework.amqp.core.Message;
import org.springframework.amqp.core.MessageListener;
import org.springframework.amqp.support.converter.MessageConverter;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import com.bht.saigonparking.api.grpc.contact.SaigonParkingMessage;
import com.bht.saigonparking.common.constant.SaigonParkingMessageQueue;
import com.bht.saigonparking.service.contact.service.MessagingService;

import lombok.RequiredArgsConstructor;

/**
 *
 * @author bht
 */
@Component
@RequiredArgsConstructor(onConstructor = @__(@Autowired))
public class SaigonParkingQueueMessageListener implements MessageListener {

    private final MessagingService messagingService;
    private final MessageConverter messageConverter;

    @Override
    public void onMessage(@NotNull Message message) {

        /* parse receiver's user ID from message in order to process/consume message */
        String userQueueName = message.getMessageProperties().getConsumerQueue();
        Long receiverUserId = SaigonParkingMessageQueue.getUserIdFromUserQueueName(userQueueName);

        /* asynchronously consume message from queue */
        SaigonParkingMessage saigonParkingMessage = (SaigonParkingMessage) messageConverter.fromMessage(message);
        messagingService.consumeMessageFromQueue(saigonParkingMessage, receiverUserId);
    }
}

// Node: repos/cloned_ms_repos/saigonparking/service/contact-service/src/main/java/com/bht/saigonparking/service/contact/listener/SaigonParkingQueueMessageListener.java:SaigonParkingQueueMessageListener.<init>
package com.bht.saigonparking.service.contact.handler;

import static com.bht.saigonparking.service.contact.configuration.WebSocketConfiguration.*;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

import org.springframework.amqp.rabbit.listener.AbstractMessageListenerContainer;
import org.springframework.context.annotation.Lazy;
import org.springframework.lang.NonNull;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.WebSocketSession;

import com.bht.saigonparking.common.constant.SaigonParkingMessageQueue;

import lombok.RequiredArgsConstructor;

/**
 *
 * @author bht
 */
@Component
@RequiredArgsConstructor(onConstructor = @__(@Lazy)) /* deal with circular dependencies injection */
public class WebSocketUserSessionManagement {

    private final Map<Long, Set<WebSocketSession>> userSessionMap = new HashMap<>(); /* is a map of <userId, session> */
    private final AbstractMessageListenerContainer messageListenerContainer;

    @Async
    public void addNewUserSession(@NonNull Long userId, @NonNull WebSocketSession webSocketSession) {

        if (userSessionMap.containsKey(userId)) {
            userSessionMap.get(userId).add(webSocketSession);

        } else {

            Set<WebSocketSession> sessionSet = new HashSet<>();
            sessionSet.add(webSocketSession);
            userSessionMap.put(userId, sessionSet);
        }
    }

    @Async
    public void removeUserSession(@NonNull Long userId, @NonNull WebSocketSession webSocketSession) {

        if (userSessionMap.containsKey(userId)) {
            boolean isCurrentSessionAuxiliary = getUserAuxiliaryFromSession(webSocketSession);
            Set<WebSocketSession> sessionSet = userSessionMap.get(userId);
            sessionSet.remove(webSocketSession);

            if (sessionSet.isEmpty()) {
                userSessionMap.remove(userId);
                if (!isCurrentSessionAuxiliary) {
                    messageListenerContainer.removeQueueNames(SaigonParkingMessageQueue.getUserQueueName(userId));
                }
            } else {
                Set<Boolean> isSessionAuxiliarySet = sessionSet.stream().map(this::getUserAuxiliaryFromSession).collect(Collectors.toSet());
                if (!isCurrentSessionAuxiliary && isSessionAuxiliarySet.size() == 1 && isSessionAuxiliarySet.contains(Boolean.TRUE)) {
                    messageListenerContainer.removeQueueNames(SaigonParkingMessageQueue.getUserQueueName(userId));
                }
            }
        }
    }

    public Set<WebSocketSession> getAllSessionOfUser(@NonNull Long userId) {
        return userSessionMap.get(userId);
    }

    public Long getUserIdFromSession(@NonNull WebSocketSession webSocketSession) {
        return (Long) webSocketSession.getAttributes().get(SAIGON_PARKING_USER_ID_KEY);
    }

    public String getUserRoleFromSession(@NonNull WebSocketSession webSocketSession) {
        return (String) webSocketSession.getAttributes().get(SAIGON_PARKING_USER_ROLE_KEY);
    }

    public boolean getUserAuxiliaryFromSession(@NonNull WebSocketSession webSocketSession) {
        return (boolean) webSocketSession.getAttributes().get(SAIGON_PARKING_USER_AUXILIARY_KEY);
    }

    public Long getParkingLotIdFromSession(@NonNull WebSocketSession webSocketSession) {
        return (Long) webSocketSession.getAttributes().get(SAIGON_PARKING_PARKING_LOT_ID_KEY);
    }
}

// Node: repos/cloned_ms_repos/saigonparking/service/contact-service/src/main/java/com/bht/saigonparking/service/contact/handler/WebSocketUserSessionManagement.java:WebSocketUserSessionManagement.<init>
package com.bht.saigonparking.emulator.configuration;

import java.io.IOException;
import java.util.concurrent.TimeUnit;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.core.io.Resource;
import org.springframework.stereotype.Component;

import com.bht.saigonparking.emulator.interceptor.AuthTokenProvideInterceptor;

import io.grpc.ManagedChannel;
import io.grpc.netty.GrpcSslContexts;
import io.grpc.netty.NettyChannelBuilder;

/**
 * config gRPC channel
 *
 * @author bht
 */
@Component
public final class ChannelConfiguration {

    /**
     *
     * channel is the abstraction to connect to a service endpoint
     * note for gRPC stub:
     *      .newStub(channel)          --> nonblocking/asynchronous stub
     *      .newBlockingStub(channel)  --> blocking/synchronous stub
     */
    @Bean
    public ManagedChannel managedChannel(@Value("${gateway.connection.host}") String host,
                                         @Value("${gateway.connection.port.grpc}") int port,
                                         @Value("${gateway.connection.idle-timeout}") int timeout,
                                         @Value("${gateway.connection.max-inbound-message-size}") int maxInBoundMessageSize,
                                         @Value("${gateway.connection.max-inbound-metadata-size}") int maxInBoundMetadataSize,
                                         @Value("${gateway.connection.certificate-path}") Resource certificate,
                                         @Autowired AuthTokenProvideInterceptor authTokenProvideInterceptor) throws IOException {

        NettyChannelBuilder channelBuilder = (host.equals("localhost"))                                 // if host is localhost means local development
                ? NettyChannelBuilder.forAddress(host, port).usePlaintext()                             // use plain-text on development environment
                : NettyChannelBuilder.forAddress(host, port).useTransportSecurity()                     // use SSL on production environment
                .sslContext(GrpcSslContexts.forClient().trustManager(certificate.getFile()).build());   // Build gRPC SSL context with cert

        return channelBuilder
                .keepAliveWithoutCalls(false)                                   // Close channel when client has already received response
                .idleTimeout(timeout, TimeUnit.MILLISECONDS)                    // 10000 milliseconds / 1000 = 10 seconds --> request time-out
                .maxInboundMessageSize(maxInBoundMessageSize * 1024 * 1024)     // 10KB * 1024 = 10MB --> max message size to transfer together
                .maxInboundMetadataSize(maxInBoundMetadataSize * 1024 * 1024)   // 2KB * 1024 = 2MB --> max message header size
                .intercept(authTokenProvideInterceptor)                         // Interceptor for providing token per each request
                .build();                                                       // Build channel to communicate over gRPC
    }
}

// Node: repos/cloned_ms_repos/saigonparking/emulator/src/main/java/com/bht/saigonparking/emulator/configuration/ChannelConfiguration.java:ChannelConfiguration.<init>
// Node: forAddress
// Node: useTransportSecurity
// Node: sslContext
// Node: forClient
// Node: trustManager
package com.bht.saigonparking.emulator.configuration;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;

import com.bht.saigonparking.api.grpc.auth.AuthServiceGrpc;
import com.bht.saigonparking.api.grpc.booking.BookingServiceGrpc;
import com.bht.saigonparking.api.grpc.contact.ContactServiceGrpc;
import com.bht.saigonparking.api.grpc.parkinglot.ParkingLotServiceGrpc;
import com.bht.saigonparking.api.grpc.parkinglot.ParkingLotServiceGrpc.ParkingLotServiceBlockingStub;
import com.bht.saigonparking.api.grpc.user.UserServiceGrpc;
import com.bht.saigonparking.api.grpc.user.UserServiceGrpc.UserServiceBlockingStub;

import io.grpc.ManagedChannel;

/**
 *
 * @author bht
 */
@Configuration
@Import(ChannelConfiguration.class)
@ComponentScan(basePackages = AppConfiguration.BASE_PACKAGE_SERVER)
public class AppConfiguration {

    static final String BASE_PACKAGE_SERVER = "com.bht.saigonparking.emulator"; // base package of EMULATOR module, contains all

    @Bean
    public UserServiceBlockingStub userServiceBlockingStub(@Autowired ManagedChannel channel) {
        return UserServiceGrpc.newBlockingStub(channel);
    }

    @Bean
    public ParkingLotServiceBlockingStub parkingLotServiceBlockingStub(@Autowired ManagedChannel channel) {
        return ParkingLotServiceGrpc.newBlockingStub(channel);
    }

    @Bean
    public AuthServiceGrpc.AuthServiceBlockingStub authServiceBlockingStub(@Autowired ManagedChannel channel) {
        return AuthServiceGrpc.newBlockingStub(channel);
    }

    @Bean
    public ContactServiceGrpc.ContactServiceBlockingStub contactServiceBlockingStub(@Autowired ManagedChannel channel) {
        return ContactServiceGrpc.newBlockingStub(channel);
    }

    @Bean
    public BookingServiceGrpc.BookingServiceBlockingStub bookingServiceBlockingStub(@Autowired ManagedChannel channel) {
        return BookingServiceGrpc.newBlockingStub(channel);
    }
}

// Node: authServiceBlockingStub
// Node: contactServiceBlockingStub
