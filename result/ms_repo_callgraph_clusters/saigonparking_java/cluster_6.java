// Cluster 6

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

// Node: repos/cloned_ms_repos/saigonparking/common/src/main/java/com/bht/saigonparking/common/interceptor/SaigonParkingServerInterceptor.java:SaigonParkingServerInterceptor.<init>
// Node: key
// Node: SaigonParkingServerInterceptor
// Node: SaigonParkingAuthenticationImpl
// Node: add
// Node: interceptCall
// Node: getMethodDescriptor
// Node: getFullMethodName
// Node: contains
package com.bht.saigonparking.common.interceptor;

import static com.bht.saigonparking.common.constant.SaigonParkingTransactionalMetadata.INTERNAL_KEY_NAME;

import io.grpc.CallOptions;
import io.grpc.Channel;
import io.grpc.ClientCall;
import io.grpc.ClientInterceptor;
import io.grpc.ForwardingClientCall;
import io.grpc.Metadata;
import io.grpc.Metadata.Key;
import io.grpc.MethodDescriptor;
import lombok.AllArgsConstructor;

/**
 *
 * This interceptor is using in gRPC client side
 *
 * Each internal service has to use this common interceptor
 * So as other internal service can recognize without authentication
 * Each internal service has to init this as Spring Bean
 * So as to easily reuse later with {@code @Autowired } injecting bean
 *
 * Remember to use the one-argument public constructor instead
 * That is {@code InternalServiceProvideInterceptor(Long internalServiceCode) }
 * internalServiceCode is the code of the service using this interceptor
 * this code will be used for internal credentials recognized !
 *
 * @author bht
 */
@AllArgsConstructor
public final class SaigonParkingClientInterceptor implements ClientInterceptor {

    private final Long internalServiceCode;
    private static final Key<String> INTERNAL_SERVICE_KEY = Key.of(INTERNAL_KEY_NAME, Metadata.ASCII_STRING_MARSHALLER);

    public static final Long INTERNAL_CODE_AUTH_SERVICE = 165305061220760001L;
    public static final Long INTERNAL_CODE_USER_SERVICE = 165305061220760002L;
    public static final Long INTERNAL_CODE_PARKING_LOT_SERVICE = 165305061220760003L;
    public static final Long INTERNAL_CODE_MAIL_SERVICE = 165305061220760004L;
    public static final Long INTERNAL_CODE_CONTACT_SERVICE = 165305061220760005L;
    public static final Long INTERNAL_CODE_BOOKING_SERVICE = 165305061220760006L;

    @Override
    public <ReqT, RespT> ClientCall<ReqT, RespT> interceptCall(MethodDescriptor<ReqT, RespT> methodDescriptor,
                                                               CallOptions callOptions,
                                                               Channel channel) {

        return new ForwardingClientCall.SimpleForwardingClientCall<ReqT, RespT>(channel.newCall(methodDescriptor, callOptions)) {
            @Override
            public void start(Listener<RespT> responseListener, Metadata headers) {
                headers.put(INTERNAL_SERVICE_KEY, internalServiceCode.toString());
                super.start(responseListener, headers);
            }
        };
    }
}

// Node: repos/cloned_ms_repos/saigonparking/common/src/main/java/com/bht/saigonparking/common/interceptor/SaigonParkingClientInterceptor.java:SaigonParkingClientInterceptor.<init>
// Node: InternalServiceProvideInterceptor
// Node: newCall
// Node: start
// Node: put
package com.bht.saigonparking.common.loadbalance;

import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.URI;
import java.util.ArrayList;
import java.util.List;

import org.apache.logging.log4j.Level;
import org.springframework.cloud.client.ServiceInstance;
import org.springframework.cloud.client.discovery.DiscoveryClient;

import com.bht.saigonparking.common.util.LoggingUtil;

import io.grpc.Attributes;
import io.grpc.EquivalentAddressGroup;
import io.grpc.NameResolver;
import lombok.Getter;

/**
 *
 * @author bht
 */
@Getter
public final class SaigonParkingNameResolver extends NameResolver {

    private final URI consulURI;
    private final String serviceId;
    private final DiscoveryClient discoveryClient;

    private Listener listener;
    private List<ServiceInstance> serviceInstances;

    public SaigonParkingNameResolver(DiscoveryClient discoveryClient,
                                     URI consulURI,
                                     String serviceId) {
        this.consulURI = consulURI;
        this.serviceId = serviceId;
        this.discoveryClient = discoveryClient;
    }

    @Override
    public String getServiceAuthority() {
        return consulURI.getAuthority();
    }

    @Override
    public void start(Listener2 listener) {
        this.listener = listener;
        loadServiceInstances();
    }

    @Override
    public void shutdown() {
        // implement shutdown...
    }

    private void loadServiceInstances() {

        List<EquivalentAddressGroup> addressList = new ArrayList<>();
        serviceInstances = discoveryClient.getInstances(serviceId);

        if (serviceInstances == null || serviceInstances.isEmpty()) {
            LoggingUtil.log(Level.WARN, "loadServiceInstances", "Warning",
                    String.format("no serviceInstances of %s", serviceId));
            return;
        }

        serviceInstances.forEach(serviceInstance -> {
            String host = serviceInstance.getHost();
            int port = serviceInstance.getPort();

            LoggingUtil.log(Level.INFO, "loadServiceInstances", serviceId, String.format("%s:%d", host, port));

            List<SocketAddress> socketAddressList = new ArrayList<>();
            socketAddressList.add(new InetSocketAddress(host, port));
            addressList.add(new EquivalentAddressGroup(socketAddressList));
        });

        if (!addressList.isEmpty()) {
            listener.onAddresses(addressList, Attributes.EMPTY);
        }
    }
}

// Node: loadServiceInstances
// Node: getInstances
// Node: forEach
// Node: getHost
// Node: getPort
// Node: InetSocketAddress
// Node: EquivalentAddressGroup
// Node: onAddresses
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

// Node: repos/cloned_ms_repos/saigonparking/service/auth-service/src/main/java/com/bht/saigonparking/service/auth/interceptor/AuthServiceInterceptor.java:AuthServiceInterceptor.<init>
// Node: AuthServiceInterceptor
package com.bht.saigonparking.service.auth.configuration;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.transaction.annotation.EnableTransactionManagement;

import com.bht.saigonparking.common.auth.SaigonParkingAuthentication;
import com.bht.saigonparking.common.auth.SaigonParkingAuthenticationImpl;
import com.bht.saigonparking.common.base.BaseSaigonParkingAppConfiguration;
import com.bht.saigonparking.common.interceptor.SaigonParkingClientInterceptor;
import com.bht.saigonparking.common.spring.SpringBeanLifeCycle;

/**
 *
 * @author bht
 */
@EnableAsync
@Configuration
@EnableTransactionManagement
@Import(ChannelConfiguration.class)
@ComponentScan(basePackages = AppConfiguration.BASE_PACKAGE)
public class AppConfiguration extends BaseSaigonParkingAppConfiguration {

    public static final String BASE_PACKAGE = "com.bht.saigonparking.service.auth"; // base package of auth module, contains all

    @Bean
    public SpringBeanLifeCycle springBeanLifeCycle() {
        return new SpringBeanLifeCycle(BASE_PACKAGE);
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Bean
    public SaigonParkingAuthentication saigonParkingBaseAuthentication() {
        return new SaigonParkingAuthenticationImpl();
    }

    @Bean
    public SaigonParkingClientInterceptor saigonParkingClientInterceptor() {
        return new SaigonParkingClientInterceptor(SaigonParkingClientInterceptor.INTERNAL_CODE_AUTH_SERVICE);
    }
}

// Node: saigonParkingBaseAuthentication
package com.bht.saigonparking.service.auth.configuration;

import java.util.HashMap;
import java.util.Map;

import org.hibernate.dialect.SQLServerDialect;
import org.hibernate.dialect.function.StandardSQLFunction;
import org.hibernate.type.Type;

/**
 * Custom SQL Server Dialect
 * Extends from Hibernate SQL Server Dialect
 * This class will be called on hibernate init
 * Register all user-defined functions here!
 *
 * @author bht
 */
public final class CustomSQLServerDialect extends SQLServerDialect {

    public CustomSQLServerDialect() {
        super();
        Map<String, Type> userDefinedFunctions = registeredUserDefinedFunctions();
        userDefinedFunctions.forEach((func, type) ->
                registerFunction(func, new StandardSQLFunction(func, type)));
    }

    private Map<String, Type> registeredUserDefinedFunctions() {
        return new HashMap<>();
    }
}

// Node: CustomSQLServerDialect
// Node: registeredUserDefinedFunctions
// Node: registerFunction
// Node: StandardSQLFunction
package com.bht.saigonparking.service.parkinglot.configuration;

import javax.persistence.EntityNotFoundException;

import org.lognet.springboot.grpc.GRpcGlobalInterceptor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.dao.EmptyResultDataAccessException;
import org.springframework.orm.ObjectOptimisticLockingFailureException;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.transaction.annotation.EnableTransactionManagement;

import com.bht.saigonparking.common.annotation.InheritedComponent;
import com.bht.saigonparking.common.base.BaseSaigonParkingAppConfiguration;
import com.bht.saigonparking.common.exception.PermissionDeniedException;
import com.bht.saigonparking.common.interceptor.SaigonParkingClientInterceptor;
import com.bht.saigonparking.common.interceptor.SaigonParkingServerInterceptor;
import com.bht.saigonparking.common.spring.SpringBeanLifeCycle;
import com.google.common.collect.ImmutableMap;

/**
 *
 * @author bht
 */
@EnableAsync
@Configuration
@EnableTransactionManagement
@Import({AwsConfiguration.class, ChannelConfiguration.class})
@ComponentScan(basePackages = AppConfiguration.BASE_PACKAGE,
        includeFilters = @ComponentScan.Filter(InheritedComponent.class))
public class AppConfiguration extends BaseSaigonParkingAppConfiguration {

    public static final String BASE_PACKAGE = "com.bht.saigonparking.service.parkinglot";

    @Bean
    public SpringBeanLifeCycle springBeanLifeCycle() {
        return new SpringBeanLifeCycle(BASE_PACKAGE);
    }

    @Bean
    public SaigonParkingClientInterceptor saigonParkingClientInterceptor() {
        return new SaigonParkingClientInterceptor(SaigonParkingClientInterceptor.INTERNAL_CODE_PARKING_LOT_SERVICE);
    }

    @Bean
    @GRpcGlobalInterceptor
    public SaigonParkingServerInterceptor saigonParkingServerInterceptor() {
        return new SaigonParkingServerInterceptor(new ImmutableMap.Builder<Class<? extends Throwable>, String>()
                .put(EntityNotFoundException.class, "SPE#00008")
                .put(DataIntegrityViolationException.class, "SPE#00009")
                .put(PermissionDeniedException.class, "SPE#00015")
                .put(ObjectOptimisticLockingFailureException.class, "SPE#00016")
                .put(EmptyResultDataAccessException.class, "SPE#00018")
                .build());
    }
}

// Node: saigonParkingServerInterceptor
package com.bht.saigonparking.service.parkinglot.configuration;

import java.util.HashMap;
import java.util.Map;

import org.hibernate.dialect.SQLServerDialect;
import org.hibernate.dialect.function.StandardSQLFunction;
import org.hibernate.type.StandardBasicTypes;
import org.hibernate.type.Type;

/**
 * Custom SQL Server Dialect
 * Extends from Hibernate SQL Server Dialect
 * This class will be called on hibernate init
 * Register all user-defined functions here!
 *
 * @author bht
 */
public final class CustomSQLServerDialect extends SQLServerDialect {

    public CustomSQLServerDialect() {
        super();

        Map<String, Type> userDefinedFunctions = registeredUserDefinedFunctions();
        userDefinedFunctions.forEach((func, type) ->
                registerFunction(func, new StandardSQLFunction(func, type)));
    }

    private Map<String, Type> registeredUserDefinedFunctions() {

        Map<String, Type> functions = new HashMap<>();
        functions.put("dbo.CALCULATE_DELTA_LAT_IN_DEGREE", StandardBasicTypes.DOUBLE);
        functions.put("dbo.CALCULATE_DELTA_LNG_IN_DEGREE", StandardBasicTypes.DOUBLE);
        functions.put("dbo.GET_DISTANCE_IN_KILOMETRE", StandardBasicTypes.DOUBLE);
        functions.put("dbo.IS_VALUE_IN_BOUND", StandardBasicTypes.BOOLEAN);
        functions.put("dbo.CHECK_AVAILABILITY", StandardBasicTypes.BOOLEAN);

        return functions;
    }
}

// Node: initParkingLotTypeBiMap
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

// Node: getParkingLotTypeByType
// Node: findByType
package com.bht.saigonparking.service.parkinglot.repository.core;

import java.util.Optional;

import javax.validation.constraints.NotEmpty;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.bht.saigonparking.service.parkinglot.entity.ParkingLotTypeEntity;

/**
 *
 * @author bht
 */
@Repository
public interface ParkingLotTypeRepository extends JpaRepository<ParkingLotTypeEntity, Long> {

    Optional<ParkingLotTypeEntity> findByType(@NotEmpty String type);
}

// Node: repos/cloned_ms_repos/saigonparking/service/parkinglot-service/src/main/java/com/bht/saigonparking/service/parkinglot/repository/core/ParkingLotTypeRepository.java:ParkingLotTypeRepository.<init>
package com.bht.saigonparking.service.user.configuration;

import javax.persistence.EntityNotFoundException;

import org.lognet.springboot.grpc.GRpcGlobalInterceptor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.dao.EmptyResultDataAccessException;
import org.springframework.orm.ObjectOptimisticLockingFailureException;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.transaction.annotation.EnableTransactionManagement;

import com.bht.saigonparking.common.annotation.InheritedComponent;
import com.bht.saigonparking.common.base.BaseSaigonParkingAppConfiguration;
import com.bht.saigonparking.common.exception.PermissionDeniedException;
import com.bht.saigonparking.common.exception.UsernameNotMatchException;
import com.bht.saigonparking.common.interceptor.SaigonParkingClientInterceptor;
import com.bht.saigonparking.common.interceptor.SaigonParkingServerInterceptor;
import com.bht.saigonparking.common.spring.SpringBeanLifeCycle;
import com.google.common.collect.ImmutableMap;


/**
 *
 * @author bht
 */
@EnableAsync
@Configuration
@EnableTransactionManagement
@Import(MessageQueueConfiguration.class)
@ComponentScan(basePackages = AppConfiguration.BASE_PACKAGE, includeFilters = @ComponentScan.Filter(InheritedComponent.class))
public class AppConfiguration extends BaseSaigonParkingAppConfiguration {

    public static final String BASE_PACKAGE = "com.bht.saigonparking.service.user";

    @Bean
    public SpringBeanLifeCycle springBeanLifeCycle() {
        return new SpringBeanLifeCycle(BASE_PACKAGE);
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Bean
    public SaigonParkingClientInterceptor saigonParkingClientInterceptor() {
        return new SaigonParkingClientInterceptor(SaigonParkingClientInterceptor.INTERNAL_CODE_USER_SERVICE);
    }

    @Bean
    @GRpcGlobalInterceptor
    public SaigonParkingServerInterceptor saigonParkingServerInterceptor() {
        return new SaigonParkingServerInterceptor(new ImmutableMap.Builder<Class<? extends Throwable>, String>()
                .put(EntityNotFoundException.class, "SPE#00008")
                .put(DataIntegrityViolationException.class, "SPE#00009")
                .put(UsernameNotMatchException.class, "SPE#00014")
                .put(PermissionDeniedException.class, "SPE#00015")
                .put(ObjectOptimisticLockingFailureException.class, "SPE#00016")
                .put(EmptyResultDataAccessException.class, "SPE#00018")
                .build());
    }
}

package com.bht.saigonparking.service.user.configuration;

import java.util.HashMap;
import java.util.Map;

import org.hibernate.dialect.SQLServerDialect;
import org.hibernate.dialect.function.StandardSQLFunction;
import org.hibernate.type.Type;

/**
 * Custom SQL Server Dialect
 * Extends from Hibernate SQL Server Dialect
 * This class will be called on hibernate init
 * Register all user-defined functions here!
 *
 * @author bht
 */
public final class CustomSQLServerDialect extends SQLServerDialect {

    public CustomSQLServerDialect() {
        super();
        Map<String, Type> userDefinedFunctions = registeredUserDefinedFunctions();
        userDefinedFunctions.forEach((func, type) ->
                registerFunction(func, new StandardSQLFunction(func, type)));
    }

    private Map<String, Type> registeredUserDefinedFunctions() {
        return new HashMap<>();
    }
}

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

// Node: getUserRoleByRoleName
// Node: findByRole
package com.bht.saigonparking.service.user.repository.core;

import java.util.Optional;

import javax.validation.constraints.NotEmpty;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.bht.saigonparking.service.user.entity.UserRoleEntity;

/**
 *
 * @author bht
 */
@Repository
public interface UserRoleRepository extends JpaRepository<UserRoleEntity, Long> {

    Optional<UserRoleEntity> findByRole(@NotEmpty String role);
}

// Node: repos/cloned_ms_repos/saigonparking/service/user-service/src/main/java/com/bht/saigonparking/service/user/repository/core/UserRoleRepository.java:UserRoleRepository.<init>
package com.bht.saigonparking.service.booking.configuration;

import javax.persistence.EntityNotFoundException;

import org.lognet.springboot.grpc.GRpcGlobalInterceptor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.dao.EmptyResultDataAccessException;
import org.springframework.orm.ObjectOptimisticLockingFailureException;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.transaction.annotation.EnableTransactionManagement;

import com.bht.saigonparking.common.annotation.InheritedComponent;
import com.bht.saigonparking.common.base.BaseSaigonParkingAppConfiguration;
import com.bht.saigonparking.common.exception.BookingAlreadyFinishedException;
import com.bht.saigonparking.common.exception.BookingAlreadyRatedException;
import com.bht.saigonparking.common.exception.BookingNotYetAcceptedException;
import com.bht.saigonparking.common.exception.BookingNotYetFinishedException;
import com.bht.saigonparking.common.exception.BookingNotYetRatedException;
import com.bht.saigonparking.common.exception.CustomerHasOnGoingBookingException;
import com.bht.saigonparking.common.exception.PermissionDeniedException;
import com.bht.saigonparking.common.interceptor.SaigonParkingClientInterceptor;
import com.bht.saigonparking.common.interceptor.SaigonParkingServerInterceptor;
import com.bht.saigonparking.common.spring.SpringBeanLifeCycle;
import com.google.common.collect.ImmutableMap;
import com.google.zxing.qrcode.QRCodeWriter;

/**
 *
 * @author bht
 */
@EnableAsync
@Configuration
@EnableTransactionManagement
@Import({ChannelConfiguration.class, MessageQueueConfiguration.class})
@ComponentScan(basePackages = AppConfiguration.BASE_PACKAGE, includeFilters = @ComponentScan.Filter(InheritedComponent.class))
public class AppConfiguration extends BaseSaigonParkingAppConfiguration {

    public static final String BASE_PACKAGE = "com.bht.saigonparking.service.booking";

    @Bean
    public QRCodeWriter qrCodeWriter() {
        return new QRCodeWriter();
    }

    @Bean
    public SpringBeanLifeCycle springBeanLifeCycle() {
        return new SpringBeanLifeCycle(BASE_PACKAGE);
    }

    @Bean
    public SaigonParkingClientInterceptor saigonParkingClientInterceptor() {
        return new SaigonParkingClientInterceptor(SaigonParkingClientInterceptor.INTERNAL_CODE_BOOKING_SERVICE);
    }

    @Bean
    @GRpcGlobalInterceptor
    public SaigonParkingServerInterceptor saigonParkingServerInterceptor() {
        return new SaigonParkingServerInterceptor(
                new ImmutableMap.Builder<Class<? extends Throwable>, String>()
                        .put(EntityNotFoundException.class, "SPE#00008")
                        .put(DataIntegrityViolationException.class, "SPE#00009")
                        .put(PermissionDeniedException.class, "SPE#00015")
                        .put(ObjectOptimisticLockingFailureException.class, "SPE#00016")
                        .put(EmptyResultDataAccessException.class, "SPE#00018")
                        .put(BookingAlreadyFinishedException.class, "SPE#00019")
                        .put(CustomerHasOnGoingBookingException.class, "SPE#00020")
                        .put(BookingNotYetAcceptedException.class, "SPE#00021")
                        .put(BookingAlreadyRatedException.class, "SPE#00022")
                        .put(BookingNotYetRatedException.class, "SPE#00023")
                        .put(BookingNotYetFinishedException.class, "SPE#00024")
                        .build());
    }
}

// Node: createOneOrManyParkingLotStatistic
// Node: deleteOneOrManyParkingLotStatistic
package com.bht.saigonparking.service.booking.configuration;

import java.util.HashMap;
import java.util.Map;

import org.hibernate.dialect.SQLServerDialect;
import org.hibernate.dialect.function.StandardSQLFunction;
import org.hibernate.type.Type;

/**
 * Custom SQL Server Dialect
 * Extends from Hibernate SQL Server Dialect
 * This class will be called on hibernate init
 * Register all user-defined functions here!
 *
 * @author bht
 */
public final class CustomSQLServerDialect extends SQLServerDialect {

    public CustomSQLServerDialect() {
        super();
        Map<String, Type> userDefinedFunctions = registeredUserDefinedFunctions();
        userDefinedFunctions.forEach((func, type) ->
                registerFunction(func, new StandardSQLFunction(func, type)));
    }

    private Map<String, Type> registeredUserDefinedFunctions() {
        return new HashMap<>();
    }
}

// Node: initBookingStatusBiMap
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

// Node: getBookingStatusByStatus
// Node: findByStatus
package com.bht.saigonparking.service.booking.repository.core;

import java.util.Optional;

import javax.validation.constraints.NotEmpty;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.bht.saigonparking.service.booking.entity.BookingStatusEntity;

/**
 *
 * @author bht
 */
@Repository
public interface BookingStatusRepository extends JpaRepository<BookingStatusEntity, Long> {

    Optional<BookingStatusEntity> findByStatus(@NotEmpty String status);
}

// Node: repos/cloned_ms_repos/saigonparking/service/booking-service/src/main/java/com/bht/saigonparking/service/booking/repository/core/BookingStatusRepository.java:BookingStatusRepository.<init>
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

package com.bht.saigonparking.service.contact.configuration;

import javax.persistence.EntityNotFoundException;

import org.lognet.springboot.grpc.GRpcGlobalInterceptor;
import org.springframework.amqp.support.converter.MessageConverter;
import org.springframework.amqp.support.converter.SimpleMessageConverter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.dao.EmptyResultDataAccessException;
import org.springframework.orm.ObjectOptimisticLockingFailureException;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.transaction.annotation.EnableTransactionManagement;
import org.springframework.web.socket.config.annotation.EnableWebSocket;

import com.bht.saigonparking.common.annotation.InheritedComponent;
import com.bht.saigonparking.common.auth.SaigonParkingAuthentication;
import com.bht.saigonparking.common.auth.SaigonParkingAuthenticationImpl;
import com.bht.saigonparking.common.base.BaseSaigonParkingAppConfiguration;
import com.bht.saigonparking.common.exception.PermissionDeniedException;
import com.bht.saigonparking.common.exception.UsernameNotMatchException;
import com.bht.saigonparking.common.interceptor.SaigonParkingClientInterceptor;
import com.bht.saigonparking.common.interceptor.SaigonParkingServerInterceptor;
import com.bht.saigonparking.common.spring.SpringBeanLifeCycle;
import com.google.common.collect.ImmutableMap;
import com.google.zxing.qrcode.QRCodeWriter;


/**
 *
 * @author bht
 */
@EnableAsync
@Configuration
@EnableWebSocket
@EnableTransactionManagement
@Import({WebSocketConfiguration.class, MessageQueueConfiguration.class, ChannelConfiguration.class})
@ComponentScan(basePackages = AppConfiguration.BASE_PACKAGE, includeFilters = @ComponentScan.Filter(InheritedComponent.class))
public class AppConfiguration extends BaseSaigonParkingAppConfiguration {

    public static final String BASE_PACKAGE = "com.bht.saigonparking.service.contact";

    @Bean
    public QRCodeWriter qrCodeWriter() {
        return new QRCodeWriter();
    }

    @Bean
    public SpringBeanLifeCycle springBeanLifeCycle() {
        return new SpringBeanLifeCycle(BASE_PACKAGE);
    }

    @Bean
    public MessageConverter messageConverter() {
        return new SimpleMessageConverter();
    }

    @Bean
    public SaigonParkingAuthentication saigonParkingBaseAuthentication() {
        return new SaigonParkingAuthenticationImpl();
    }

    @Bean
    public SaigonParkingClientInterceptor saigonParkingClientInterceptor() {
        return new SaigonParkingClientInterceptor(SaigonParkingClientInterceptor.INTERNAL_CODE_CONTACT_SERVICE);
    }

    @Bean
    @GRpcGlobalInterceptor
    public SaigonParkingServerInterceptor saigonParkingServerInterceptor() {
        return new SaigonParkingServerInterceptor(new ImmutableMap.Builder<Class<? extends Throwable>, String>()
                .put(EntityNotFoundException.class, "SPE#00008")
                .put(DataIntegrityViolationException.class, "SPE#00009")
                .put(UsernameNotMatchException.class, "SPE#00014")
                .put(PermissionDeniedException.class, "SPE#00015")
                .put(ObjectOptimisticLockingFailureException.class, "SPE#00016")
                .put(EmptyResultDataAccessException.class, "SPE#00018")
                .build());
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

