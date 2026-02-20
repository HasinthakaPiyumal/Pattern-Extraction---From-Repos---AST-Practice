// Cluster 12

// Node: get
// Node: emptyMap
// Node: MissingTokenException
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

// Node: UsernameNotMatchException
// Node: toString
package com.bht.saigonparking.common.base;

import java.io.IOException;

import javax.annotation.PostConstruct;
import javax.annotation.PreDestroy;

/**
 * Saigon Parking Project Base Bean
 *
 * @author bht
 */
public interface BaseBean {

    /**
     * This method will be called
     * as the bean has been initialized
     */
    @PostConstruct
    default void initialize() throws IOException {
    }

    /**
     * This method will be called
     * as the bean is about to be destroyed
     */
    @PreDestroy
    default void destroy() {
    }
}

// Node: repos/cloned_ms_repos/saigonparking/common/src/main/java/com/bht/saigonparking/common/base/BaseBean.java:BaseBean.<init>
// Node: initialize
package com.bht.saigonparking.common.base;

import javax.persistence.EntityManager;
import javax.persistence.PersistenceContext;
import javax.persistence.criteria.CriteriaBuilder;

/**
 *
 * Base Repository Custom Class
 *
 * Repository Custom Class is using for
 * extend original JPA Repository Interface
 * which means self-implement more methods
 * and/or complex, nested queries,...
 * that cannot achieve by usual JPA method
 *
 * How to setup ?
 * 1. interface XRepository will extends interface JpaRepository
 * 2. interface XRepository will extends interface XRepositoryCustom too
 *    --> in order to inherit all of methods inside interface XRCustom
 * 3. class XRepositoryCustomImpl will extends BaseRepositoryCustom
 * 4. class XRepositoryCustomImpl of course will implements XRepositoryCustom
 * 5. mark them with {@code @Repository} for Spring to init them as beans
 *
 * @author bht
 */
public abstract class BaseRepositoryCustom implements BaseBean {

    /**
     *
     * Each EntityManager instance
     * is associated with a persistence context.
     *
     * Within the persistence context,
     * the entity instances and their lifecycle are managed.
     *
     * Persistence context defines a scope under
     * which particular entity instances are created, persisted, or removed.
     *
     * A persistence context is like a cache
     * which contains a set of persistent entities ,
     * So once the transaction is finished,
     * all persistent objects are detached
     * from the EntityManager's persistence context
     * and are no longer managed.
     */
    @PersistenceContext
    protected EntityManager entityManager;

    protected CriteriaBuilder criteriaBuilder;

    @Override
    public void initialize() {
        criteriaBuilder = entityManager.getCriteriaBuilder();
    }

    protected String convertKeyword(String keyword) {
        return "%" + keyword + "%";
    }
}

// Node: getCriteriaBuilder
package com.bht.saigonparking.common.base;

import java.util.Map;

import org.apache.logging.log4j.Level;
import org.springframework.http.HttpStatus;
import org.springframework.http.server.ServerHttpRequest;
import org.springframework.http.server.ServerHttpResponse;
import org.springframework.lang.NonNull;
import org.springframework.web.socket.WebSocketHandler;
import org.springframework.web.socket.server.support.HttpSessionHandshakeInterceptor;

import com.bht.saigonparking.common.auth.SaigonParkingAuthentication;
import com.bht.saigonparking.common.auth.SaigonParkingTokenBody;
import com.bht.saigonparking.common.exception.MissingTokenException;
import com.bht.saigonparking.common.util.LoggingUtil;

import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.MalformedJwtException;
import io.jsonwebtoken.io.DecodingException;
import io.jsonwebtoken.security.SignatureException;
import lombok.NoArgsConstructor;

/**
 *
 * @author bht
 */
@NoArgsConstructor
public abstract class BaseWebSocketHandshakeInterceptor extends HttpSessionHandshakeInterceptor implements BaseBean {

    protected abstract SaigonParkingAuthentication getAuthentication();

    protected abstract String getAccessTokenFromHttpRequest(@NonNull ServerHttpRequest httpRequest);

    protected abstract void postAuthentication(@NonNull SaigonParkingTokenBody saigonParkingTokenBody,
                                               @NonNull Map<String, Object> webSocketSessionAttributes);

    @Override
    public final boolean beforeHandshake(@NonNull ServerHttpRequest httpRequest,
                                         @NonNull ServerHttpResponse httpResponse,
                                         @NonNull WebSocketHandler webSocketHandler,
                                         @NonNull Map<String, Object> attributes) throws Exception {
        try {
            String accessToken = getAccessTokenFromHttpRequest(httpRequest);
            SaigonParkingTokenBody saigonParkingTokenBody = getAuthentication().parseJwtToken(accessToken);
            postAuthentication(saigonParkingTokenBody, attributes);

        } catch (ExpiredJwtException expiredJwtException) {
            LoggingUtil.log(Level.ERROR, "WebSocketInterceptor", "Exception", "ExpiredJwtException");
            httpResponse.setStatusCode(HttpStatus.UNAUTHORIZED);
            return false;

        } catch (SignatureException signatureException) {
            LoggingUtil.log(Level.ERROR, "WebSocketInterceptor", "Exception", "SignatureException");
            httpResponse.setStatusCode(HttpStatus.UNAUTHORIZED);
            return false;

        } catch (MalformedJwtException malformedJwtException) {
            LoggingUtil.log(Level.ERROR, "WebSocketInterceptor", "Exception", "MalformedJwtException");
            httpResponse.setStatusCode(HttpStatus.UNAUTHORIZED);
            return false;

        } catch (DecodingException decodingException) {
            LoggingUtil.log(Level.ERROR, "WebSocketInterceptor", "Exception", "DecodingException");
            httpResponse.setStatusCode(HttpStatus.UNAUTHORIZED);
            return false;

        } catch (MissingTokenException missingTokenException) {
            LoggingUtil.log(Level.ERROR, "WebSocketInterceptor", "Exception", "MissingTokenException");
            httpResponse.setStatusCode(HttpStatus.UNAUTHORIZED);
            return false;

        } catch (Exception exception) {
            LoggingUtil.log(Level.ERROR, "WebSocketInterceptor", "Exception", exception.getClass().getSimpleName());
            httpResponse.setStatusCode(HttpStatus.INTERNAL_SERVER_ERROR);
            return false;
        }
        return super.beforeHandshake(httpRequest, httpResponse, webSocketHandler, attributes);
    }
}

// Node: repos/cloned_ms_repos/saigonparking/common/src/main/java/com/bht/saigonparking/common/base/BaseWebSocketHandshakeInterceptor.java:BaseWebSocketHandshakeInterceptor.<init>
// Node: getAuthentication
// Node: getAccessTokenFromHttpRequest
// Node: postAuthentication
// Node: beforeHandshake
// Node: setStatusCode
package com.bht.saigonparking.common.spring;

import java.io.IOException;
import java.lang.reflect.Proxy;

import org.apache.logging.log4j.Level;
import org.springframework.beans.factory.config.DestructionAwareBeanPostProcessor;
import org.springframework.lang.NonNull;

import com.bht.saigonparking.common.base.BaseBean;
import com.bht.saigonparking.common.util.LoggingUtil;

import lombok.AllArgsConstructor;


/**
 *
 * Hook into the life cycle of each spring bean (create, destroy,...)
 *
 * @author bht
 */
@AllArgsConstructor
public final class SpringBeanLifeCycle implements BaseBean, DestructionAwareBeanPostProcessor {

    private final String moduleBasePackage;

    @Override
    public void initialize() throws IOException {
        BaseBean.super.initialize();
        LoggingUtil.log(Level.INFO, "SPRING", "BeanCreation", "springBeanLifeCycle");
    }


    @Override
    public void destroy() {
        BaseBean.super.destroy();
        LoggingUtil.log(Level.INFO, "SPRING", "BeanDestruction", "springBeanLifeCycle");
    }


    @Override
    public Object postProcessBeforeInitialization(@NonNull Object bean, @NonNull String beanName) {
        if (!(bean instanceof Proxy) && bean.getClass().getPackage().getName().startsWith(moduleBasePackage)) {
            LoggingUtil.log(Level.INFO, "SPRING", "BeanCreation", beanName);
        }
        return DestructionAwareBeanPostProcessor.super.postProcessBeforeInitialization(bean, beanName);
    }


    @Override
    public void postProcessBeforeDestruction(@NonNull Object bean, @NonNull String beanName) {
        if (!(bean instanceof Proxy) && bean.getClass().getPackage().getName().startsWith(moduleBasePackage)) {
            LoggingUtil.log(Level.INFO, "SPRING", "BeanDestruction", beanName);
        }
    }
}

// Node: repos/cloned_ms_repos/saigonparking/common/src/main/java/com/bht/saigonparking/common/spring/SpringBeanLifeCycle.java:SpringBeanLifeCycle.<init>
// Node: bean
// Node: isEmpty
// Node: convertAndSend
// Node: SuppressWarnings
package com.bht.saigonparking.service.parkinglot.mapper;

import java.util.List;
import java.util.stream.Collectors;

import javax.persistence.Tuple;
import javax.validation.constraints.NotNull;

import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.Named;
import org.mapstruct.NullValueMappingStrategy;
import org.springframework.stereotype.Component;

import com.bht.saigonparking.api.grpc.parkinglot.ParkingLot;
import com.bht.saigonparking.api.grpc.parkinglot.ParkingLotInformation;
import com.bht.saigonparking.api.grpc.parkinglot.ParkingLotResult;
import com.bht.saigonparking.service.parkinglot.configuration.AppConfiguration;
import com.bht.saigonparking.service.parkinglot.entity.ParkingLotEntity;
import com.bht.saigonparking.service.parkinglot.entity.ParkingLotInformationEntity;
import com.bht.saigonparking.service.parkinglot.entity.ParkingLotLimitEntity;

/**
 *
 * Mapper class for parking-lot entities and its families
 * Mapper is used for mapping objects from different layers
 * For example here is: map Entity obj to DTO obj and vice versa
 *
 * @author bht
 */
@Component
@SuppressWarnings("UnmappedTargetProperties")
@Mapper(componentModel = "spring", implementationPackage = AppConfiguration.BASE_PACKAGE + ".mapper.impl",
        nullValueMappingStrategy = NullValueMappingStrategy.RETURN_DEFAULT,
        uses = {EnumMapper.class, CustomizedMapper.class})
public interface ParkingLotMapper {

    @Named("toParkingLotResultWithoutName")
    @Mapping(target = "id", expression = "java(parkingLotWithoutNameTuple.get(0, java.math.BigInteger.class).longValue())")
    @Mapping(target = "type", expression = "java(enumMapper.toParkingLotType(parkingLotWithoutNameTuple.get(1, java.math.BigInteger.class).longValue()))")
    @Mapping(target = "latitude", expression = "java(parkingLotWithoutNameTuple.get(2, Double.class))")
    @Mapping(target = "longitude", expression = "java(parkingLotWithoutNameTuple.get(3, Double.class))")
    @Mapping(target = "availableSlot", expression = "java(parkingLotWithoutNameTuple.get(4, Short.class))")
    @Mapping(target = "totalSlot", expression = "java(parkingLotWithoutNameTuple.get(5, Short.class))")
    ParkingLotResult toParkingLotResultWithoutName(@NotNull Tuple parkingLotWithoutNameTuple);

    @Named("toParkingLotResultWithName")
    @Mapping(target = "id", expression = "java(parkingLotWithNameTuple.get(0, java.math.BigInteger.class).longValue())")
    @Mapping(target = "name", expression = "java(parkingLotWithNameTuple.get(1, String.class))")
    @Mapping(target = "type", expression = "java(enumMapper.toParkingLotType(parkingLotWithNameTuple.get(2, java.math.BigInteger.class).longValue()))")
    @Mapping(target = "latitude", expression = "java(parkingLotWithNameTuple.get(3, Double.class))")
    @Mapping(target = "longitude", expression = "java(parkingLotWithNameTuple.get(4, Double.class))")
    @Mapping(target = "availableSlot", expression = "java(parkingLotWithNameTuple.get(5, Short.class))")
    @Mapping(target = "totalSlot", expression = "java(parkingLotWithNameTuple.get(6, Short.class))")
    ParkingLotResult toParkingLotResultWithName(@NotNull Tuple parkingLotWithNameTuple);

    @Named("toParkingLotInformation")
    @Mapping(target = "name", source = "name", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    @Mapping(target = "address", source = "address", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    @Mapping(target = "phone", source = "phone", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    @Mapping(target = "imageData", source = "id", qualifiedByName = "toEncodedParkingLotImage", defaultExpression = "java(customizedMapper.DEFAULT_BYTE_STRING_VALUE)")
    @Mapping(target = "version", source = "version", defaultExpression = "java(customizedMapper.DEFAULT_LONG_VALUE)")
    ParkingLotInformation toParkingLotInformation(@NotNull ParkingLotInformationEntity parkingLotInformationEntity);

    @Named("toParkingLotInformationIgnoreImage")
    @Mapping(target = "name", source = "name", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    @Mapping(target = "address", source = "address", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    @Mapping(target = "phone", source = "phone", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    @Mapping(target = "imageData", expression = "java(customizedMapper.DEFAULT_BYTE_STRING_VALUE)")
    @Mapping(target = "version", source = "version", defaultExpression = "java(customizedMapper.DEFAULT_LONG_VALUE)")
    ParkingLotInformation toParkingLotInformationIgnoreImage(@NotNull ParkingLotInformationEntity parkingLotInformationEntity);

    @Named("toParkingLot")
    @Mapping(target = "id", source = "id", defaultExpression = "java(customizedMapper.DEFAULT_LONG_VALUE)")
    @Mapping(target = "information", source = "parkingLotInformationEntity", qualifiedByName = "toParkingLotInformation", defaultExpression = "java(customizedMapper.DEFAULT_PARKING_LOT_INFORMATION)")
    @Mapping(target = "type", source = "parkingLotTypeEntity", qualifiedByName = "toParkingLotType", defaultExpression = "java(customizedMapper.DEFAULT_PARKING_LOT_TYPE)")
    @Mapping(target = "latitude", source = "latitude", defaultExpression = "java(customizedMapper.DEFAULT_DOUBLE_VALUE)")
    @Mapping(target = "longitude", source = "longitude", defaultExpression = "java(customizedMapper.DEFAULT_DOUBLE_VALUE)")
    @Mapping(target = "openingHour", source = "openingHour", qualifiedByName = "toTimeString", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    @Mapping(target = "closingHour", source = "closingHour", qualifiedByName = "toTimeString", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    @Mapping(target = "availableSlot", source = "parkingLotLimitEntity.availableSlot", defaultExpression = "java(customizedMapper.DEFAULT_SHORT_VALUE)")
    @Mapping(target = "totalSlot", source = "parkingLotLimitEntity.totalSlot", defaultExpression = "java(customizedMapper.DEFAULT_SHORT_VALUE)")
    @Mapping(target = "version", source = "version", defaultExpression = "java(customizedMapper.DEFAULT_LONG_VALUE)")
    ParkingLot toParkingLot(@NotNull ParkingLotEntity parkingLotEntity);

    @Named("toParkingLotIgnoreImage")
    @Mapping(target = "id", source = "id", defaultExpression = "java(customizedMapper.DEFAULT_LONG_VALUE)")
    @Mapping(target = "information", source = "parkingLotInformationEntity", qualifiedByName = "toParkingLotInformationIgnoreImage", defaultExpression = "java(customizedMapper.DEFAULT_PARKING_LOT_INFORMATION)")
    @Mapping(target = "type", source = "parkingLotTypeEntity", qualifiedByName = "toParkingLotType", defaultExpression = "java(customizedMapper.DEFAULT_PARKING_LOT_TYPE)")
    @Mapping(target = "latitude", source = "latitude", defaultExpression = "java(customizedMapper.DEFAULT_DOUBLE_VALUE)")
    @Mapping(target = "longitude", source = "longitude", defaultExpression = "java(customizedMapper.DEFAULT_DOUBLE_VALUE)")
    @Mapping(target = "openingHour", source = "openingHour", qualifiedByName = "toTimeString", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    @Mapping(target = "closingHour", source = "closingHour", qualifiedByName = "toTimeString", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    @Mapping(target = "availableSlot", source = "parkingLotLimitEntity.availableSlot", defaultExpression = "java(customizedMapper.DEFAULT_SHORT_VALUE)")
    @Mapping(target = "totalSlot", source = "parkingLotLimitEntity.totalSlot", defaultExpression = "java(customizedMapper.DEFAULT_SHORT_VALUE)")
    @Mapping(target = "version", source = "version", defaultExpression = "java(customizedMapper.DEFAULT_LONG_VALUE)")
    ParkingLot toParkingLotIgnoreImage(@NotNull ParkingLotEntity parkingLotEntity);

    @Named("toParkingLotLimitEntityIgnoreParkingLotEntity")
    @Mapping(target = "parkingLotEntity", ignore = true)
    @Mapping(target = "id", ignore = true)
    @Mapping(target = "version", ignore = true)
    @Mapping(target = "totalSlot", source = "totalSlot", defaultExpression = "java(customizedMapper.DEFAULT_SHORT_VALUE)")
    @Mapping(target = "availableSlot", source = "availableSlot", defaultExpression = "java(customizedMapper.DEFAULT_SHORT_VALUE)")
    ParkingLotLimitEntity toParkingLotLimitEntityIgnoreParkingLotEntity(@NotNull ParkingLot parkingLot);

    @Named("toParkingLotInformationEntityIgnoreParkingLotEntity")
    @Mapping(target = "parkingLotEntity", ignore = true)
    @Mapping(target = "id", ignore = true)
    @Mapping(target = "version", ignore = true)
    @Mapping(target = "name", source = "information.name", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    @Mapping(target = "phone", source = "information.phone", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    @Mapping(target = "address", source = "information.address", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    ParkingLotInformationEntity toParkingLotInformationEntityIgnoreParkingLotEntity(@NotNull ParkingLot parkingLot);

    @Named("toParkingLotResultListWithoutName")
    default List<ParkingLotResult> toParkingLotResultListWithoutName(@NotNull List<Tuple> parkingLotWithoutNameTupleList) {
        return parkingLotWithoutNameTupleList.stream().map(this::toParkingLotResultWithoutName).collect(Collectors.toList());
    }

    @Named("toParkingLotResultListWithName")
    default List<ParkingLotResult> toParkingLotResultListWithName(@NotNull List<Tuple> parkingLotWithNameTupleList) {
        return parkingLotWithNameTupleList.stream().map(this::toParkingLotResultWithName).collect(Collectors.toList());
    }

    @Named("toParkingLotList")
    default List<ParkingLot> toParkingLotList(@NotNull List<ParkingLotEntity> parkingLotEntityList) {
        return parkingLotEntityList.stream().map(this::toParkingLotIgnoreImage).collect(Collectors.toList());
    }
}

// Node: repos/cloned_ms_repos/saigonparking/service/parkinglot-service/src/main/java/com/bht/saigonparking/service/parkinglot/mapper/ParkingLotMapper.java:for.<init>
// Node: Named
// Node: Mapping
// Node: java
// Node: longValue
// Node: toParkingLotType
// Node: toParkingLotResultWithoutName
// Node: toParkingLotResultWithName
// Node: toParkingLotInformation
// Node: toParkingLotInformationIgnoreImage
// Node: toParkingLotIgnoreImage
// Node: toParkingLotLimitEntityIgnoreParkingLotEntity
// Node: toParkingLotInformationEntityIgnoreParkingLotEntity
// Node: stream
// Node: map
// Node: collect
// Node: toList
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

// Node: initParkingLotTypeValueMap
// Node: initParkingLotTypeMap
// Node: toParkingLotTypeEntity
// Node: inverse
// Node: toParkingLotTypeValue
// Node: putAll
// Node: entrySet
// Node: toMap
// Node: getKey
// Node: getNumber
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

// Node: toTimeString
// Node: toTimestampString
package com.bht.saigonparking.service.parkinglot.repository.custom.impl;

import java.sql.Time;
import java.time.LocalTime;
import java.util.List;

import javax.persistence.Tuple;
import javax.persistence.TypedQuery;
import javax.persistence.criteria.CriteriaQuery;
import javax.persistence.criteria.Fetch;
import javax.persistence.criteria.Join;
import javax.persistence.criteria.JoinType;
import javax.persistence.criteria.Root;
import javax.validation.constraints.Max;
import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;

import org.springframework.stereotype.Repository;

import com.bht.saigonparking.common.base.BaseEntity_;
import com.bht.saigonparking.common.base.BaseRepositoryCustom;
import com.bht.saigonparking.service.parkinglot.entity.ParkingLotEntity;
import com.bht.saigonparking.service.parkinglot.entity.ParkingLotEntity_;
import com.bht.saigonparking.service.parkinglot.entity.ParkingLotInformationEntity;
import com.bht.saigonparking.service.parkinglot.entity.ParkingLotInformationEntity_;
import com.bht.saigonparking.service.parkinglot.entity.ParkingLotTypeEntity;
import com.bht.saigonparking.service.parkinglot.repository.custom.ParkingLotRepositoryCustom;

/**
 *
 * @author bht
 */
@Repository
@SuppressWarnings("unchecked")
public class ParkingLotRepositoryCustomImpl extends BaseRepositoryCustom implements ParkingLotRepositoryCustom {

    @Override
    public List<Tuple> countAllParkingLotGroupByType() {
        String getCountGroupByQuery = "SELECT P.parkingLotTypeEntity.id, COUNT(P.id) " +
                "FROM ParkingLotEntity P " +
                "GROUP BY P.parkingLotTypeEntity.id ";

        return entityManager.createQuery(getCountGroupByQuery, Tuple.class)
                .getResultList();
    }

    @Override
    public Long countAll() {

        CriteriaQuery<Long> query = criteriaBuilder.createQuery(Long.class);
        Root<ParkingLotEntity> root = query.from(ParkingLotEntity.class);

        return entityManager.createQuery(query
                .select(criteriaBuilder.count(root)))
                .getSingleResult();
    }

    @Override
    public Long countAll(boolean isAvailable) {

        CriteriaQuery<Long> query = criteriaBuilder.createQuery(Long.class);
        Root<ParkingLotEntity> root = query.from(ParkingLotEntity.class);
        Time currentTime = Time.valueOf(LocalTime.now());

        return entityManager.createQuery(query
                .select(criteriaBuilder.count(root))
                .where(isAvailable
                        ? criteriaBuilder.and(
                        criteriaBuilder.equal(root.get(ParkingLotEntity_.isAvailable), true),
                        criteriaBuilder.lessThanOrEqualTo(root.get(ParkingLotEntity_.openingHour), currentTime),
                        criteriaBuilder.greaterThanOrEqualTo(root.get(ParkingLotEntity_.closingHour), currentTime))
                        : criteriaBuilder.or(
                        criteriaBuilder.equal(root.get(ParkingLotEntity_.isAvailable), false),
                        criteriaBuilder.greaterThan(root.get(ParkingLotEntity_.openingHour), criteriaBuilder.currentTime()),
                        criteriaBuilder.lessThan(root.get(ParkingLotEntity_.closingHour), criteriaBuilder.currentTime()))))
                .getSingleResult();
    }

    @Override
    public Long countAll(@NotEmpty String keyword) {

        CriteriaQuery<Long> query = criteriaBuilder.createQuery(Long.class);
        Root<ParkingLotEntity> root = query.from(ParkingLotEntity.class);

        Join<ParkingLotEntity, ParkingLotInformationEntity> parkingLotInformationEntityJoin = root
                .join(ParkingLotEntity_.parkingLotInformationEntity, JoinType.LEFT);

        return entityManager.createQuery(query
                .select(criteriaBuilder.count(root))
                .where(criteriaBuilder.or(
                        criteriaBuilder.like(parkingLotInformationEntityJoin.get(ParkingLotInformationEntity_.name), convertKeyword(keyword)),
                        criteriaBuilder.like(parkingLotInformationEntityJoin.get(ParkingLotInformationEntity_.address), convertKeyword(keyword)),
                        criteriaBuilder.like(parkingLotInformationEntityJoin.get(ParkingLotInformationEntity_.phone), convertKeyword(keyword)))))
                .getSingleResult();
    }

    @Override
    public Long countAll(@NotNull ParkingLotTypeEntity parkingLotTypeEntity) {

        CriteriaQuery<Long> query = criteriaBuilder.createQuery(Long.class);
        Root<ParkingLotEntity> root = query.from(ParkingLotEntity.class);

        Join<ParkingLotEntity, ParkingLotTypeEntity> parkingLotTypeEntityJoin = root
                .join(ParkingLotEntity_.parkingLotTypeEntity, JoinType.LEFT);

        return entityManager.createQuery(query
                .select(criteriaBuilder.count(root))
                .where(criteriaBuilder.equal(parkingLotTypeEntityJoin.get(BaseEntity_.id), parkingLotTypeEntity.getId())))
                .getSingleResult();
    }

    @Override
    public Long countAll(@NotEmpty String keyword, boolean isAvailable) {

        CriteriaQuery<Long> query = criteriaBuilder.createQuery(Long.class);
        Root<ParkingLotEntity> root = query.from(ParkingLotEntity.class);
        Time currentTime = Time.valueOf(LocalTime.now());

        Join<ParkingLotEntity, ParkingLotInformationEntity> parkingLotInformationEntityJoin = root
                .join(ParkingLotEntity_.parkingLotInformationEntity, JoinType.LEFT);

        return entityManager.createQuery(query
                .select(criteriaBuilder.count(root))
                .where(criteriaBuilder.and(
                        isAvailable
                                ? criteriaBuilder.and(
                                criteriaBuilder.equal(root.get(ParkingLotEntity_.isAvailable), true),
                                criteriaBuilder.lessThanOrEqualTo(root.get(ParkingLotEntity_.openingHour), currentTime),
                                criteriaBuilder.greaterThanOrEqualTo(root.get(ParkingLotEntity_.closingHour), currentTime))
                                : criteriaBuilder.or(
                                criteriaBuilder.equal(root.get(ParkingLotEntity_.isAvailable), false),
                                criteriaBuilder.greaterThan(root.get(ParkingLotEntity_.openingHour), criteriaBuilder.currentTime()),
                                criteriaBuilder.lessThan(root.get(ParkingLotEntity_.closingHour), criteriaBuilder.currentTime())),
                        criteriaBuilder.or(
                                criteriaBuilder.like(parkingLotInformationEntityJoin.get(ParkingLotInformationEntity_.name), convertKeyword(keyword)),
                                criteriaBuilder.like(parkingLotInformationEntityJoin.get(ParkingLotInformationEntity_.address), convertKeyword(keyword)),
                                criteriaBuilder.like(parkingLotInformationEntityJoin.get(ParkingLotInformationEntity_.phone), convertKeyword(keyword))))))
                .getSingleResult();
    }

    @Override
    public Long countAll(@NotNull ParkingLotTypeEntity parkingLotTypeEntity, boolean isAvailable) {

        CriteriaQuery<Long> query = criteriaBuilder.createQuery(Long.class);
        Root<ParkingLotEntity> root = query.from(ParkingLotEntity.class);
        Time currentTime = Time.valueOf(LocalTime.now());

        Join<ParkingLotEntity, ParkingLotTypeEntity> parkingLotTypeEntityJoin = root
                .join(ParkingLotEntity_.parkingLotTypeEntity, JoinType.LEFT);

        return entityManager.createQuery(query
                .select(criteriaBuilder.count(root))
                .where(criteriaBuilder.and(
                        criteriaBuilder.equal(parkingLotTypeEntityJoin.get(BaseEntity_.id), parkingLotTypeEntity.getId()),
                        isAvailable
                                ? criteriaBuilder.and(
                                criteriaBuilder.equal(root.get(ParkingLotEntity_.isAvailable), true),
                                criteriaBuilder.lessThanOrEqualTo(root.get(ParkingLotEntity_.openingHour), currentTime),
                                criteriaBuilder.greaterThanOrEqualTo(root.get(ParkingLotEntity_.closingHour), currentTime))
                                : criteriaBuilder.or(
                                criteriaBuilder.equal(root.get(ParkingLotEntity_.isAvailable), false),
                                criteriaBuilder.greaterThan(root.get(ParkingLotEntity_.openingHour), criteriaBuilder.currentTime()),
                                criteriaBuilder.lessThan(root.get(ParkingLotEntity_.closingHour), criteriaBuilder.currentTime())))))
                .getSingleResult();
    }

    @Override
    public Long countAll(@NotEmpty String keyword, @NotNull ParkingLotTypeEntity parkingLotTypeEntity) {

        CriteriaQuery<Long> query = criteriaBuilder.createQuery(Long.class);
        Root<ParkingLotEntity> root = query.from(ParkingLotEntity.class);

        Join<ParkingLotEntity, ParkingLotTypeEntity> parkingLotTypeEntityJoin = root
                .join(ParkingLotEntity_.parkingLotTypeEntity, JoinType.LEFT);
        Join<ParkingLotEntity, ParkingLotInformationEntity> parkingLotInformationEntityJoin = root
                .join(ParkingLotEntity_.parkingLotInformationEntity, JoinType.LEFT);

        return entityManager.createQuery(query
                .select(criteriaBuilder.count(root))
                .where(criteriaBuilder.and(
                        criteriaBuilder.equal(parkingLotTypeEntityJoin.get(BaseEntity_.id), parkingLotTypeEntity.getId()),
                        criteriaBuilder.or(
                                criteriaBuilder.like(parkingLotInformationEntityJoin.get(ParkingLotInformationEntity_.name), convertKeyword(keyword)),
                                criteriaBuilder.like(parkingLotInformationEntityJoin.get(ParkingLotInformationEntity_.address), convertKeyword(keyword)),
                                criteriaBuilder.like(parkingLotInformationEntityJoin.get(ParkingLotInformationEntity_.phone), convertKeyword(keyword))))))
                .getSingleResult();
    }

    @Override
    public Long countAll(@NotEmpty String keyword, @NotNull ParkingLotTypeEntity parkingLotTypeEntity, boolean isAvailable) {

        CriteriaQuery<Long> query = criteriaBuilder.createQuery(Long.class);
        Root<ParkingLotEntity> root = query.from(ParkingLotEntity.class);
        Time currentTime = Time.valueOf(LocalTime.now());

        Join<ParkingLotEntity, ParkingLotTypeEntity> parkingLotTypeEntityJoin = root
                .join(ParkingLotEntity_.parkingLotTypeEntity, JoinType.LEFT);
        Join<ParkingLotEntity, ParkingLotInformationEntity> parkingLotInformationEntityJoin = root
                .join(ParkingLotEntity_.parkingLotInformationEntity, JoinType.LEFT);

        return entityManager.createQuery(query
                .select(criteriaBuilder.count(root))
                .where(criteriaBuilder.and(
                        criteriaBuilder.equal(parkingLotTypeEntityJoin.get(BaseEntity_.id), parkingLotTypeEntity.getId()),
                        isAvailable
                                ? criteriaBuilder.and(
                                criteriaBuilder.equal(root.get(ParkingLotEntity_.isAvailable), true),
                                criteriaBuilder.lessThanOrEqualTo(root.get(ParkingLotEntity_.openingHour), currentTime),
                                criteriaBuilder.greaterThanOrEqualTo(root.get(ParkingLotEntity_.closingHour), currentTime))
                                : criteriaBuilder.or(
                                criteriaBuilder.equal(root.get(ParkingLotEntity_.isAvailable), false),
                                criteriaBuilder.greaterThan(root.get(ParkingLotEntity_.openingHour), criteriaBuilder.currentTime()),
                                criteriaBuilder.lessThan(root.get(ParkingLotEntity_.closingHour), criteriaBuilder.currentTime())),
                        criteriaBuilder.or(
                                criteriaBuilder.like(parkingLotInformationEntityJoin.get(ParkingLotInformationEntity_.name), convertKeyword(keyword)),
                                criteriaBuilder.like(parkingLotInformationEntityJoin.get(ParkingLotInformationEntity_.address), convertKeyword(keyword)),
                                criteriaBuilder.like(parkingLotInformationEntityJoin.get(ParkingLotInformationEntity_.phone), convertKeyword(keyword))))))
                .getSingleResult();
    }

    @Override
    public List<ParkingLotEntity> getAll(@NotNull @Max(20L) Integer nRow, @NotNull Integer pageNumber) {

        CriteriaQuery<ParkingLotEntity> query = criteriaBuilder.createQuery(ParkingLotEntity.class);
        Root<ParkingLotEntity> root = query.from(ParkingLotEntity.class);

        root.fetch(ParkingLotEntity_.parkingLotTypeEntity);
        root.fetch(ParkingLotEntity_.parkingLotLimitEntity);
        root.fetch(ParkingLotEntity_.parkingLotInformationEntity);

        TypedQuery<ParkingLotEntity> getAllQuery = entityManager
                .createQuery(query
                        .select(root)
                        .orderBy(criteriaBuilder.asc(root)));

        getAllQuery.setMaxResults(nRow);
        getAllQuery.setFirstResult(nRow * (pageNumber - 1));

        return getAllQuery.getResultList();
    }

    @Override
    public List<ParkingLotEntity> getAll(@NotNull @Max(20L) Integer nRow, @NotNull Integer pageNumber, boolean isAvailable) {

        CriteriaQuery<ParkingLotEntity> query = criteriaBuilder.createQuery(ParkingLotEntity.class);
        Root<ParkingLotEntity> root = query.from(ParkingLotEntity.class);
        Time currentTime = Time.valueOf(LocalTime.now());

        root.fetch(ParkingLotEntity_.parkingLotTypeEntity);
        root.fetch(ParkingLotEntity_.parkingLotLimitEntity);
        root.fetch(ParkingLotEntity_.parkingLotInformationEntity);

        TypedQuery<ParkingLotEntity> getAllQuery = entityManager
                .createQuery(query
                        .select(root)
                        .where(isAvailable
                                ? criteriaBuilder.and(
                                criteriaBuilder.equal(root.get(ParkingLotEntity_.isAvailable), true),
                                criteriaBuilder.lessThanOrEqualTo(root.get(ParkingLotEntity_.openingHour), currentTime),
                                criteriaBuilder.greaterThanOrEqualTo(root.get(ParkingLotEntity_.closingHour), currentTime))
                                : criteriaBuilder.or(
                                criteriaBuilder.equal(root.get(ParkingLotEntity_.isAvailable), false),
                                criteriaBuilder.greaterThan(root.get(ParkingLotEntity_.openingHour), criteriaBuilder.currentTime()),
                                criteriaBuilder.lessThan(root.get(ParkingLotEntity_.closingHour), criteriaBuilder.currentTime())))
                        .orderBy(criteriaBuilder.asc(root)));

        getAllQuery.setMaxResults(nRow);
        getAllQuery.setFirstResult(nRow * (pageNumber - 1));

        return getAllQuery.getResultList();
    }

    @Override
    public List<ParkingLotEntity> getAll(@NotNull @Max(20L) Integer nRow, @NotNull Integer pageNumber, @NotEmpty String keyword) {

        CriteriaQuery<ParkingLotEntity> query = criteriaBuilder.createQuery(ParkingLotEntity.class);
        Root<ParkingLotEntity> root = query.from(ParkingLotEntity.class);

        root.fetch(ParkingLotEntity_.parkingLotTypeEntity);
        root.fetch(ParkingLotEntity_.parkingLotLimitEntity);
        Fetch<ParkingLotEntity, ParkingLotInformationEntity> parkingLotInformationEntityFetch = root
                .fetch(ParkingLotEntity_.parkingLotInformationEntity);
        Join<ParkingLotEntity, ParkingLotInformationEntity> parkingLotInformationEntityJoin =
                (Join<ParkingLotEntity, ParkingLotInformationEntity>) parkingLotInformationEntityFetch;

        TypedQuery<ParkingLotEntity> getAllQuery = entityManager
                .createQuery(query
                        .select(root)
                        .where(criteriaBuilder.or(
                                criteriaBuilder.like(parkingLotInformationEntityJoin.get(ParkingLotInformationEntity_.name), convertKeyword(keyword)),
                                criteriaBuilder.like(parkingLotInformationEntityJoin.get(ParkingLotInformationEntity_.address), convertKeyword(keyword)),
                                criteriaBuilder.like(parkingLotInformationEntityJoin.get(ParkingLotInformationEntity_.phone), convertKeyword(keyword))))
                        .orderBy(criteriaBuilder.asc(root)));

        getAllQuery.setMaxResults(nRow);
        getAllQuery.setFirstResult(nRow * (pageNumber - 1));

        return getAllQuery.getResultList();
    }

    @Override
    public List<ParkingLotEntity> getAll(@NotNull @Max(20L) Integer nRow, @NotNull Integer pageNumber, @NotNull ParkingLotTypeEntity parkingLotTypeEntity) {

        CriteriaQuery<ParkingLotEntity> query = criteriaBuilder.createQuery(ParkingLotEntity.class);
        Root<ParkingLotEntity> root = query.from(ParkingLotEntity.class);

        root.fetch(ParkingLotEntity_.parkingLotLimitEntity);
        root.fetch(ParkingLotEntity_.parkingLotInformationEntity);
        Fetch<ParkingLotEntity, ParkingLotTypeEntity> parkingLotTypeEntityFetch = root
                .fetch(ParkingLotEntity_.parkingLotTypeEntity);
        Join<ParkingLotEntity, ParkingLotTypeEntity> parkingLotTypeEntityJoin =
                (Join<ParkingLotEntity, ParkingLotTypeEntity>) parkingLotTypeEntityFetch;

        TypedQuery<ParkingLotEntity> getAllQuery = entityManager
                .createQuery(query
                        .select(root)
                        .where(criteriaBuilder.equal(parkingLotTypeEntityJoin.get(BaseEntity_.id), parkingLotTypeEntity.getId()))
                        .orderBy(criteriaBuilder.asc(root)));

        getAllQuery.setMaxResults(nRow);
        getAllQuery.setFirstResult(nRow * (pageNumber - 1));

        return getAllQuery.getResultList();
    }

    @Override
    public List<ParkingLotEntity> getAll(@NotNull @Max(20L) Integer nRow, @NotNull Integer pageNumber, @NotEmpty String keyword, boolean isAvailable) {

        CriteriaQuery<ParkingLotEntity> query = criteriaBuilder.createQuery(ParkingLotEntity.class);
        Root<ParkingLotEntity> root = query.from(ParkingLotEntity.class);
        Time currentTime = Time.valueOf(LocalTime.now());

        root.fetch(ParkingLotEntity_.parkingLotTypeEntity);
        root.fetch(ParkingLotEntity_.parkingLotLimitEntity);
        Fetch<ParkingLotEntity, ParkingLotInformationEntity> parkingLotInformationEntityFetch = root
                .fetch(ParkingLotEntity_.parkingLotInformationEntity);
        Join<ParkingLotEntity, ParkingLotInformationEntity> parkingLotInformationEntityJoin =
                (Join<ParkingLotEntity, ParkingLotInformationEntity>) parkingLotInformationEntityFetch;

        TypedQuery<ParkingLotEntity> getAllQuery = entityManager
                .createQuery(query
                        .select(root)
                        .where(criteriaBuilder.and(
                                isAvailable
                                        ? criteriaBuilder.and(
                                        criteriaBuilder.equal(root.get(ParkingLotEntity_.isAvailable), true),
                                        criteriaBuilder.lessThanOrEqualTo(root.get(ParkingLotEntity_.openingHour), currentTime),
                                        criteriaBuilder.greaterThanOrEqualTo(root.get(ParkingLotEntity_.closingHour), currentTime))
                                        : criteriaBuilder.or(
                                        criteriaBuilder.equal(root.get(ParkingLotEntity_.isAvailable), false),
                                        criteriaBuilder.greaterThan(root.get(ParkingLotEntity_.openingHour), criteriaBuilder.currentTime()),
                                        criteriaBuilder.lessThan(root.get(ParkingLotEntity_.closingHour), criteriaBuilder.currentTime())),
                                criteriaBuilder.or(
                                        criteriaBuilder.like(parkingLotInformationEntityJoin.get(ParkingLotInformationEntity_.name), convertKeyword(keyword)),
                                        criteriaBuilder.like(parkingLotInformationEntityJoin.get(ParkingLotInformationEntity_.address), convertKeyword(keyword)),
                                        criteriaBuilder.like(parkingLotInformationEntityJoin.get(ParkingLotInformationEntity_.phone), convertKeyword(keyword)))))
                        .orderBy(criteriaBuilder.asc(root)));

        getAllQuery.setMaxResults(nRow);
        getAllQuery.setFirstResult(nRow * (pageNumber - 1));

        return getAllQuery.getResultList();
    }

    @Override
    public List<ParkingLotEntity> getAll(@NotNull @Max(20L) Integer nRow, @NotNull Integer pageNumber, @NotNull ParkingLotTypeEntity parkingLotTypeEntity, boolean isAvailable) {

        CriteriaQuery<ParkingLotEntity> query = criteriaBuilder.createQuery(ParkingLotEntity.class);
        Root<ParkingLotEntity> root = query.from(ParkingLotEntity.class);
        Time currentTime = Time.valueOf(LocalTime.now());

        root.fetch(ParkingLotEntity_.parkingLotLimitEntity);
        root.fetch(ParkingLotEntity_.parkingLotInformationEntity);
        Fetch<ParkingLotEntity, ParkingLotTypeEntity> parkingLotTypeEntityFetch = root
                .fetch(ParkingLotEntity_.parkingLotTypeEntity);
        Join<ParkingLotEntity, ParkingLotTypeEntity> parkingLotTypeEntityJoin =
                (Join<ParkingLotEntity, ParkingLotTypeEntity>) parkingLotTypeEntityFetch;

        TypedQuery<ParkingLotEntity> getAllQuery = entityManager
                .createQuery(query
                        .select(root)
                        .where(criteriaBuilder.and(
                                criteriaBuilder.equal(parkingLotTypeEntityJoin.get(BaseEntity_.id), parkingLotTypeEntity.getId()),
                                isAvailable
                                        ? criteriaBuilder.and(
                                        criteriaBuilder.equal(root.get(ParkingLotEntity_.isAvailable), true),
                                        criteriaBuilder.lessThanOrEqualTo(root.get(ParkingLotEntity_.openingHour), currentTime),
                                        criteriaBuilder.greaterThanOrEqualTo(root.get(ParkingLotEntity_.closingHour), currentTime))
                                        : criteriaBuilder.or(
                                        criteriaBuilder.equal(root.get(ParkingLotEntity_.isAvailable), false),
                                        criteriaBuilder.greaterThan(root.get(ParkingLotEntity_.openingHour), criteriaBuilder.currentTime()),
                                        criteriaBuilder.lessThan(root.get(ParkingLotEntity_.closingHour), criteriaBuilder.currentTime()))))
                        .orderBy(criteriaBuilder.asc(root)));

        getAllQuery.setMaxResults(nRow);
        getAllQuery.setFirstResult(nRow * (pageNumber - 1));

        return getAllQuery.getResultList();
    }

    @Override
    public List<ParkingLotEntity> getAll(@NotNull @Max(20L) Integer nRow, @NotNull Integer pageNumber, @NotEmpty String keyword, @NotNull ParkingLotTypeEntity parkingLotTypeEntity) {

        CriteriaQuery<ParkingLotEntity> query = criteriaBuilder.createQuery(ParkingLotEntity.class);
        Root<ParkingLotEntity> root = query.from(ParkingLotEntity.class);

        root.fetch(ParkingLotEntity_.parkingLotLimitEntity);
        Fetch<ParkingLotEntity, ParkingLotTypeEntity> parkingLotTypeEntityFetch = root
                .fetch(ParkingLotEntity_.parkingLotTypeEntity);
        Join<ParkingLotEntity, ParkingLotTypeEntity> parkingLotTypeEntityJoin =
                (Join<ParkingLotEntity, ParkingLotTypeEntity>) parkingLotTypeEntityFetch;
        Fetch<ParkingLotEntity, ParkingLotInformationEntity> parkingLotInformationEntityFetch = root
                .fetch(ParkingLotEntity_.parkingLotInformationEntity);
        Join<ParkingLotEntity, ParkingLotInformationEntity> parkingLotInformationEntityJoin =
                (Join<ParkingLotEntity, ParkingLotInformationEntity>) parkingLotInformationEntityFetch;

        TypedQuery<ParkingLotEntity> getAllQuery = entityManager
                .createQuery(query
                        .select(root)
                        .where(criteriaBuilder.and(
                                criteriaBuilder.equal(parkingLotTypeEntityJoin.get(BaseEntity_.id), parkingLotTypeEntity.getId()),
                                criteriaBuilder.or(
                                        criteriaBuilder.like(parkingLotInformationEntityJoin.get(ParkingLotInformationEntity_.name), convertKeyword(keyword)),
                                        criteriaBuilder.like(parkingLotInformationEntityJoin.get(ParkingLotInformationEntity_.address), convertKeyword(keyword)),
                                        criteriaBuilder.like(parkingLotInformationEntityJoin.get(ParkingLotInformationEntity_.phone), convertKeyword(keyword)))))
                        .orderBy(criteriaBuilder.asc(root)));

        getAllQuery.setMaxResults(nRow);
        getAllQuery.setFirstResult(nRow * (pageNumber - 1));

        return getAllQuery.getResultList();
    }

    @Override
    public List<ParkingLotEntity> getAll(@NotNull @Max(20L) Integer nRow, @NotNull Integer pageNumber, @NotEmpty String keyword, @NotNull ParkingLotTypeEntity parkingLotTypeEntity, boolean isAvailable) {

        CriteriaQuery<ParkingLotEntity> query = criteriaBuilder.createQuery(ParkingLotEntity.class);
        Root<ParkingLotEntity> root = query.from(ParkingLotEntity.class);
        Time currentTime = Time.valueOf(LocalTime.now());

        root.fetch(ParkingLotEntity_.parkingLotLimitEntity);
        Fetch<ParkingLotEntity, ParkingLotTypeEntity> parkingLotTypeEntityFetch = root
                .fetch(ParkingLotEntity_.parkingLotTypeEntity);
        Join<ParkingLotEntity, ParkingLotTypeEntity> parkingLotTypeEntityJoin =
                (Join<ParkingLotEntity, ParkingLotTypeEntity>) parkingLotTypeEntityFetch;
        Fetch<ParkingLotEntity, ParkingLotInformationEntity> parkingLotInformationEntityFetch = root
                .fetch(ParkingLotEntity_.parkingLotInformationEntity);
        Join<ParkingLotEntity, ParkingLotInformationEntity> parkingLotInformationEntityJoin =
                (Join<ParkingLotEntity, ParkingLotInformationEntity>) parkingLotInformationEntityFetch;

        TypedQuery<ParkingLotEntity> getAllQuery = entityManager
                .createQuery(query
                        .select(root)
                        .where(criteriaBuilder.and(
                                criteriaBuilder.equal(parkingLotTypeEntityJoin.get(BaseEntity_.id), parkingLotTypeEntity.getId()),
                                isAvailable
                                        ? criteriaBuilder.and(
                                        criteriaBuilder.equal(root.get(ParkingLotEntity_.isAvailable), true),
                                        criteriaBuilder.lessThanOrEqualTo(root.get(ParkingLotEntity_.openingHour), currentTime),
                                        criteriaBuilder.greaterThanOrEqualTo(root.get(ParkingLotEntity_.closingHour), currentTime))
                                        : criteriaBuilder.or(
                                        criteriaBuilder.equal(root.get(ParkingLotEntity_.isAvailable), false),
                                        criteriaBuilder.greaterThan(root.get(ParkingLotEntity_.openingHour), criteriaBuilder.currentTime()),
                                        criteriaBuilder.lessThan(root.get(ParkingLotEntity_.closingHour), criteriaBuilder.currentTime())),
                                criteriaBuilder.or(
                                        criteriaBuilder.like(parkingLotInformationEntityJoin.get(ParkingLotInformationEntity_.name), convertKeyword(keyword)),
                                        criteriaBuilder.like(parkingLotInformationEntityJoin.get(ParkingLotInformationEntity_.address), convertKeyword(keyword)),
                                        criteriaBuilder.like(parkingLotInformationEntityJoin.get(ParkingLotInformationEntity_.phone), convertKeyword(keyword)))))
                        .orderBy(criteriaBuilder.asc(root)));

        getAllQuery.setMaxResults(nRow);
        getAllQuery.setFirstResult(nRow * (pageNumber - 1));

        return getAllQuery.getResultList();
    }
}

// Node: repos/cloned_ms_repos/saigonparking/service/parkinglot-service/src/main/java/com/bht/saigonparking/service/parkinglot/repository/custom/impl/ParkingLotRepositoryCustomImpl.java:ParkingLotRepositoryCustomImpl.<init>
package com.bht.saigonparking.service.parkinglot.repository.core;

import java.util.Optional;
import java.util.Set;

import javax.persistence.Tuple;
import javax.validation.constraints.NotNull;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import com.bht.saigonparking.service.parkinglot.entity.ParkingLotInformationEntity;

/**
 *
 * @author bht
 */
@Repository
public interface ParkingLotInformationRepository extends JpaRepository<ParkingLotInformationEntity, Long> {

    /**
     *
     * self-implement getById method
     * in order to prevent N+1 problem
     */
    @Query("SELECT PLI " +
            "FROM ParkingLotInformationEntity PLI " +
            "JOIN FETCH PLI.parkingLotEntity PL " +
            "JOIN FETCH PL.parkingLotTypeEntity PLT " +
            "JOIN FETCH PL.parkingLotLimitEntity PLL " +
            "WHERE PLI.id = ?1")
    ParkingLotInformationEntity getById(@NotNull Long id);

    /**
     *
     * self-implement getParkingLotNameByParkingLotId method
     */
    @Query("SELECT PLI.name FROM ParkingLotInformationEntity PLI WHERE PLI.parkingLotEntity.id = ?1")
    Optional<String> getParkingLotName(@NotNull Long parkingLotId);

    /**
     *
     * self-implement mapParkingLotNameWithId method
     * in order to prevent N+1 problem
     *
     * each tuple will contains 2 fields: parkingLotId, parkingLotName
     * tuple set will then be map into a map of <parkingLotId, parkingLotName>
     */
    @Query("SELECT PLI.parkingLotEntity.id, PLI.name " +
            "FROM ParkingLotInformationEntity PLI " +
            "WHERE PLI.parkingLotEntity.id IN ?1")
    Set<Tuple> mapParkingLotNameWithId(@NotNull Set<Long> parkingLotIdSet);
}

// Node: repos/cloned_ms_repos/saigonparking/service/parkinglot-service/src/main/java/com/bht/saigonparking/service/parkinglot/repository/core/ParkingLotInformationRepository.java:ParkingLotInformationRepository.<init>
// Node: getParkingLotName
// Node: mapParkingLotNameWithId
// Node: addAllParkingLotId
// Node: mapToParkingLotNameMap
// Node: getParkingLotNameByParkingLotId
// Node: createNewParkingLot
// Node: addAllEmployeeId
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

// Node: getParkingLotEmployeeEntitySet
// Node: toSet
// Node: addAllInfo
// Node: singleton
// Node: setParkingLotId
// Node: deleteAll
// Node: setParkingLotEntity
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

// Node: consumeMessageFromParkingLotTopic
// Node: getInfoList
// Node: deleteMultiUserById
// Node: getEmployeeIdList
// Node: deleteParkingLotEmployeesByParkingLotId
package com.bht.saigonparking.service.user.mapper;

import java.util.List;
import java.util.stream.Collectors;

import javax.validation.constraints.NotNull;

import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.Named;
import org.mapstruct.NullValueMappingStrategy;
import org.springframework.stereotype.Component;

import com.bht.saigonparking.api.grpc.user.Customer;
import com.bht.saigonparking.api.grpc.user.User;
import com.bht.saigonparking.service.user.configuration.AppConfiguration;
import com.bht.saigonparking.service.user.entity.CustomerEntity;
import com.bht.saigonparking.service.user.entity.UserEntity;

/**
 *
 * Mapper class for user entities and its families
 * Mapper is used for mapping objects from different layers
 * For example here is: map Entity obj to DTO obj and vice versa
 *
 * @author bht
 */
@Component
@SuppressWarnings("UnmappedTargetProperties")
@Mapper(componentModel = "spring",
        implementationPackage = AppConfiguration.BASE_PACKAGE + ".mapper.impl",
        nullValueMappingStrategy = NullValueMappingStrategy.RETURN_DEFAULT,
        uses = {EnumMapper.class, CustomizedMapper.class})
public interface UserMapper {

    @Named("toUser")
    @Mapping(target = "id", source = "id", defaultExpression = "java(customizedMapper.DEFAULT_LONG_VALUE)")
    @Mapping(target = "role", source = "userRoleEntity", qualifiedByName = "toUserRole", defaultExpression = "java(customizedMapper.DEFAULT_USER_ROLE)")
    @Mapping(target = "username", source = "username", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    @Mapping(target = "password", source = "password", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    @Mapping(target = "email", source = "email", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    @Mapping(target = "isActivated", source = "isActivated", defaultExpression = "java(customizedMapper.DEFAULT_BOOL_VALUE)")
    @Mapping(target = "lastSignIn", source = "lastSignIn", qualifiedByName = "toTimestampString", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    @Mapping(target = "version", source = "version", defaultExpression = "java(customizedMapper.DEFAULT_LONG_VALUE)")
    User toUser(@NotNull UserEntity userEntity);


    @Named("toUserList")
    default List<User> toUserList(@NotNull List<UserEntity> userEntityList) {
        return userEntityList.stream().map(this::toUser).collect(Collectors.toList());
    }


    @Named("toCustomer")
    @Mapping(target = "userInfo", source = "customerEntity", qualifiedByName = "toUser", defaultExpression = "java(customizedMapper.DEFAULT_USER)")
    @Mapping(target = "firstName", source = "firstName", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    @Mapping(target = "lastName", source = "lastName", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    @Mapping(target = "phone", source = "phone", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    @Mapping(target = "lastUpdated", source = "lastUpdated", qualifiedByName = "toTimestampString", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    Customer toCustomer(@NotNull CustomerEntity customerEntity);


    @Named("toCustomerWithoutUserInfo")
    @Mapping(target = "userInfo", ignore = true)
    @Mapping(target = "firstName", source = "firstName", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    @Mapping(target = "lastName", source = "lastName", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    @Mapping(target = "phone", source = "phone", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    @Mapping(target = "lastUpdated", source = "lastUpdated", qualifiedByName = "toTimestampString", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    Customer toCustomerWithoutUserInfo(@NotNull CustomerEntity customerEntity);
}

// Node: repos/cloned_ms_repos/saigonparking/service/user-service/src/main/java/com/bht/saigonparking/service/user/mapper/UserMapper.java:for.<init>
// Node: toCustomerWithoutUserInfo
// Node: toUserRoleEntity
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

// Node: initUserRoleBiMap
// Node: initUserRoleValueMap
// Node: toUserRole
// Node: toUserRoleValue
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

package com.bht.saigonparking.service.user.repository.custom.impl;

import java.util.List;

import javax.persistence.Tuple;
import javax.persistence.TypedQuery;
import javax.persistence.criteria.CriteriaQuery;
import javax.persistence.criteria.Fetch;
import javax.persistence.criteria.Join;
import javax.persistence.criteria.JoinType;
import javax.persistence.criteria.Root;
import javax.validation.constraints.Max;
import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;

import org.springframework.stereotype.Repository;

import com.bht.saigonparking.common.base.BaseEntity_;
import com.bht.saigonparking.common.base.BaseRepositoryCustom;
import com.bht.saigonparking.service.user.entity.UserEntity;
import com.bht.saigonparking.service.user.entity.UserEntity_;
import com.bht.saigonparking.service.user.entity.UserRoleEntity;
import com.bht.saigonparking.service.user.repository.custom.UserRepositoryCustom;

/**
 *
 * @author bht
 */
@Repository
@SuppressWarnings("unchecked")
public class UserRepositoryCustomImpl extends BaseRepositoryCustom implements UserRepositoryCustom {

    @Override
    public List<Tuple> countAllUserGroupByRole() {
        String getCountGroupByQuery = "SELECT U.userRoleEntity.id, COUNT(U.id) " +
                "FROM UserEntity U " +
                "GROUP BY U.userRoleEntity.id ";

        return entityManager.createQuery(getCountGroupByQuery, Tuple.class)
                .getResultList();
    }

    @Override
    public Long countAll() {

        CriteriaQuery<Long> query = criteriaBuilder.createQuery(Long.class);
        Root<UserEntity> root = query.from(UserEntity.class);

        return entityManager.createQuery(query
                .select(criteriaBuilder.count(root)))
                .getSingleResult();
    }

    @Override
    public Long countAll(@NotNull Boolean isActivated) {

        CriteriaQuery<Long> query = criteriaBuilder.createQuery(Long.class);
        Root<UserEntity> root = query.from(UserEntity.class);

        return entityManager.createQuery(query
                .select(criteriaBuilder.count(root))
                .where(criteriaBuilder.equal(root.get(UserEntity_.isActivated), isActivated)))
                .getSingleResult();
    }

    @Override
    public Long countAll(@NotEmpty String keyword) {

        CriteriaQuery<Long> query = criteriaBuilder.createQuery(Long.class);
        Root<UserEntity> root = query.from(UserEntity.class);

        return entityManager.createQuery(query
                .select(criteriaBuilder.count(root))
                .where(criteriaBuilder.or(
                        criteriaBuilder.like(root.get(UserEntity_.username), convertKeyword(keyword)),
                        criteriaBuilder.like(root.get(UserEntity_.email), convertKeyword(keyword)))))
                .getSingleResult();
    }

    @Override
    public Long countAll(@NotNull UserRoleEntity userRoleEntity) {

        CriteriaQuery<Long> query = criteriaBuilder.createQuery(Long.class);
        Root<UserEntity> root = query.from(UserEntity.class);

        Join<UserEntity, UserRoleEntity> userRoleEntityJoin = root
                .join(UserEntity_.userRoleEntity, JoinType.LEFT);

        return entityManager.createQuery(query
                .select(criteriaBuilder.count(root))
                .where(criteriaBuilder.equal(userRoleEntityJoin.get(BaseEntity_.id), userRoleEntity.getId())))
                .getSingleResult();
    }

    @Override
    public Long countAll(@NotEmpty String keyword, @NotNull Boolean isActivated) {

        CriteriaQuery<Long> query = criteriaBuilder.createQuery(Long.class);
        Root<UserEntity> root = query.from(UserEntity.class);

        return entityManager.createQuery(query
                .select(criteriaBuilder.count(root))
                .where(criteriaBuilder.and(
                        criteriaBuilder.equal(root.get(UserEntity_.isActivated), isActivated),
                        criteriaBuilder.or(
                                criteriaBuilder.like(root.get(UserEntity_.username), convertKeyword(keyword)),
                                criteriaBuilder.like(root.get(UserEntity_.email), convertKeyword(keyword))))))
                .getSingleResult();
    }

    @Override
    public Long countAll(@NotNull UserRoleEntity userRoleEntity, @NotNull Boolean isActivated) {

        CriteriaQuery<Long> query = criteriaBuilder.createQuery(Long.class);
        Root<UserEntity> root = query.from(UserEntity.class);

        Join<UserEntity, UserRoleEntity> userRoleEntityJoin = root
                .join(UserEntity_.userRoleEntity, JoinType.LEFT);

        return entityManager.createQuery(query
                .select(criteriaBuilder.count(root))
                .where(criteriaBuilder.and(
                        criteriaBuilder.equal(root.get(UserEntity_.isActivated), isActivated),
                        criteriaBuilder.equal(userRoleEntityJoin.get(BaseEntity_.id), userRoleEntity.getId()))))
                .getSingleResult();
    }

    @Override
    public Long countAll(@NotEmpty String keyword, @NotNull UserRoleEntity userRoleEntity) {

        CriteriaQuery<Long> query = criteriaBuilder.createQuery(Long.class);
        Root<UserEntity> root = query.from(UserEntity.class);

        Join<UserEntity, UserRoleEntity> userRoleEntityJoin = root
                .join(UserEntity_.userRoleEntity, JoinType.LEFT);

        return entityManager.createQuery(query
                .select(criteriaBuilder.count(root))
                .where(criteriaBuilder.and(
                        criteriaBuilder.equal(userRoleEntityJoin.get(BaseEntity_.id), userRoleEntity.getId()),
                        criteriaBuilder.or(
                                criteriaBuilder.like(root.get(UserEntity_.username), convertKeyword(keyword)),
                                criteriaBuilder.like(root.get(UserEntity_.email), convertKeyword(keyword))))))
                .getSingleResult();
    }

    @Override
    public Long countAll(@NotEmpty String keyword, @NotNull UserRoleEntity userRoleEntity, @NotNull Boolean isActivated) {

        CriteriaQuery<Long> query = criteriaBuilder.createQuery(Long.class);
        Root<UserEntity> root = query.from(UserEntity.class);

        Join<UserEntity, UserRoleEntity> userRoleEntityJoin = root
                .join(UserEntity_.userRoleEntity, JoinType.LEFT);

        return entityManager.createQuery(query
                .select(criteriaBuilder.count(root))
                .where(criteriaBuilder.and(
                        criteriaBuilder.equal(root.get(UserEntity_.isActivated), isActivated),
                        criteriaBuilder.equal(userRoleEntityJoin.get(BaseEntity_.id), userRoleEntity.getId()),
                        criteriaBuilder.or(
                                criteriaBuilder.like(root.get(UserEntity_.username), convertKeyword(keyword)),
                                criteriaBuilder.like(root.get(UserEntity_.email), convertKeyword(keyword))))))
                .getSingleResult();
    }

    @Override
    public List<UserEntity> getAll(@NotNull @Max(20L) Integer nRow, @NotNull Integer pageNumber) {

        CriteriaQuery<UserEntity> query = criteriaBuilder.createQuery(UserEntity.class);
        Root<UserEntity> root = query.from(UserEntity.class);

        root.fetch(UserEntity_.userRoleEntity);

        TypedQuery<UserEntity> getAllQuery = entityManager
                .createQuery(query
                        .select(root)
                        .orderBy(criteriaBuilder.asc(root)));

        getAllQuery.setMaxResults(nRow);
        getAllQuery.setFirstResult(nRow * (pageNumber - 1));

        return getAllQuery.getResultList();
    }

    @Override
    public List<UserEntity> getAll(@NotNull @Max(20L) Integer nRow, @NotNull Integer pageNumber, @NotNull Boolean isActivated) {

        CriteriaQuery<UserEntity> query = criteriaBuilder.createQuery(UserEntity.class);
        Root<UserEntity> root = query.from(UserEntity.class);

        root.fetch(UserEntity_.userRoleEntity);

        TypedQuery<UserEntity> getAllQuery = entityManager
                .createQuery(query
                        .select(root)
                        .where(criteriaBuilder.equal(root.get(UserEntity_.isActivated), isActivated))
                        .orderBy(criteriaBuilder.asc(root)));

        getAllQuery.setMaxResults(nRow);
        getAllQuery.setFirstResult(nRow * (pageNumber - 1));

        return getAllQuery.getResultList();
    }

    @Override
    public List<UserEntity> getAll(@NotNull @Max(20L) Integer nRow, @NotNull Integer pageNumber, @NotEmpty String keyword) {

        CriteriaQuery<UserEntity> query = criteriaBuilder.createQuery(UserEntity.class);
        Root<UserEntity> root = query.from(UserEntity.class);

        root.fetch(UserEntity_.userRoleEntity);

        TypedQuery<UserEntity> getAllQuery = entityManager
                .createQuery(query
                        .select(root)
                        .where(criteriaBuilder.or(
                                criteriaBuilder.like(root.get(UserEntity_.username), convertKeyword(keyword)),
                                criteriaBuilder.like(root.get(UserEntity_.email), convertKeyword(keyword))))
                        .orderBy(criteriaBuilder.asc(root)));

        getAllQuery.setMaxResults(nRow);
        getAllQuery.setFirstResult(nRow * (pageNumber - 1));

        return getAllQuery.getResultList();
    }

    @Override
    public List<UserEntity> getAll(@NotNull @Max(20L) Integer nRow, @NotNull Integer pageNumber, @NotNull UserRoleEntity userRoleEntity) {

        CriteriaQuery<UserEntity> query = criteriaBuilder.createQuery(UserEntity.class);
        Root<UserEntity> root = query.from(UserEntity.class);

        Fetch<UserEntity, UserRoleEntity> userRoleEntityFetch = root
                .fetch(UserEntity_.userRoleEntity);
        Join<UserEntity, UserRoleEntity> userRoleEntityJoin =
                (Join<UserEntity, UserRoleEntity>) userRoleEntityFetch;

        TypedQuery<UserEntity> getAllQuery = entityManager
                .createQuery(query
                        .select(root)
                        .where(criteriaBuilder.equal(userRoleEntityJoin.get(BaseEntity_.id), userRoleEntity.getId()))
                        .orderBy(criteriaBuilder.asc(root)));

        getAllQuery.setMaxResults(nRow);
        getAllQuery.setFirstResult(nRow * (pageNumber - 1));

        return getAllQuery.getResultList();
    }

    @Override
    public List<UserEntity> getAll(@NotNull @Max(20L) Integer nRow, @NotNull Integer pageNumber, @NotEmpty String keyword, @NotNull Boolean isActivated) {

        CriteriaQuery<UserEntity> query = criteriaBuilder.createQuery(UserEntity.class);
        Root<UserEntity> root = query.from(UserEntity.class);

        root.fetch(UserEntity_.userRoleEntity);

        TypedQuery<UserEntity> getAllQuery = entityManager
                .createQuery(query
                        .select(root)
                        .where(criteriaBuilder.and(
                                criteriaBuilder.equal(root.get(UserEntity_.isActivated), isActivated),
                                criteriaBuilder.or(
                                        criteriaBuilder.like(root.get(UserEntity_.username), convertKeyword(keyword)),
                                        criteriaBuilder.like(root.get(UserEntity_.email), convertKeyword(keyword)))))
                        .orderBy(criteriaBuilder.asc(root)));

        getAllQuery.setMaxResults(nRow);
        getAllQuery.setFirstResult(nRow * (pageNumber - 1));

        return getAllQuery.getResultList();
    }

    @Override
    public List<UserEntity> getAll(@NotNull @Max(20L) Integer nRow, @NotNull Integer pageNumber, @NotNull UserRoleEntity userRoleEntity, @NotNull Boolean isActivated) {

        CriteriaQuery<UserEntity> query = criteriaBuilder.createQuery(UserEntity.class);
        Root<UserEntity> root = query.from(UserEntity.class);

        Fetch<UserEntity, UserRoleEntity> userRoleEntityFetch = root
                .fetch(UserEntity_.userRoleEntity);
        Join<UserEntity, UserRoleEntity> userRoleEntityJoin =
                (Join<UserEntity, UserRoleEntity>) userRoleEntityFetch;

        TypedQuery<UserEntity> getAllQuery = entityManager
                .createQuery(query
                        .select(root)
                        .where(criteriaBuilder.and(
                                criteriaBuilder.equal(root.get(UserEntity_.isActivated), isActivated),
                                criteriaBuilder.equal(userRoleEntityJoin.get(BaseEntity_.id), userRoleEntity.getId())))
                        .orderBy(criteriaBuilder.asc(root)));

        getAllQuery.setMaxResults(nRow);
        getAllQuery.setFirstResult(nRow * (pageNumber - 1));

        return getAllQuery.getResultList();
    }

    @Override
    public List<UserEntity> getAll(@NotNull @Max(20L) Integer nRow, @NotNull Integer pageNumber, @NotEmpty String keyword, @NotNull UserRoleEntity userRoleEntity) {

        CriteriaQuery<UserEntity> query = criteriaBuilder.createQuery(UserEntity.class);
        Root<UserEntity> root = query.from(UserEntity.class);

        Fetch<UserEntity, UserRoleEntity> userRoleEntityFetch = root
                .fetch(UserEntity_.userRoleEntity);
        Join<UserEntity, UserRoleEntity> userRoleEntityJoin =
                (Join<UserEntity, UserRoleEntity>) userRoleEntityFetch;

        TypedQuery<UserEntity> getAllQuery = entityManager
                .createQuery(query
                        .select(root)
                        .where(criteriaBuilder.and(
                                criteriaBuilder.equal(userRoleEntityJoin.get(BaseEntity_.id), userRoleEntity.getId()),
                                criteriaBuilder.or(
                                        criteriaBuilder.like(root.get(UserEntity_.username), convertKeyword(keyword)),
                                        criteriaBuilder.like(root.get(UserEntity_.email), convertKeyword(keyword)))))
                        .orderBy(criteriaBuilder.asc(root)));

        getAllQuery.setMaxResults(nRow);
        getAllQuery.setFirstResult(nRow * (pageNumber - 1));

        return getAllQuery.getResultList();
    }

    @Override
    public List<UserEntity> getAll(@NotNull @Max(20L) Integer nRow, @NotNull Integer pageNumber, @NotEmpty String keyword, @NotNull UserRoleEntity userRoleEntity, @NotNull Boolean isActivated) {

        CriteriaQuery<UserEntity> query = criteriaBuilder.createQuery(UserEntity.class);
        Root<UserEntity> root = query.from(UserEntity.class);

        Fetch<UserEntity, UserRoleEntity> userRoleEntityFetch = root
                .fetch(UserEntity_.userRoleEntity);
        Join<UserEntity, UserRoleEntity> userRoleEntityJoin =
                (Join<UserEntity, UserRoleEntity>) userRoleEntityFetch;

        TypedQuery<UserEntity> getAllQuery = entityManager
                .createQuery(query
                        .select(root)
                        .where(criteriaBuilder.and(
                                criteriaBuilder.equal(root.get(UserEntity_.isActivated), isActivated),
                                criteriaBuilder.equal(userRoleEntityJoin.get(BaseEntity_.id), userRoleEntity.getId()),
                                criteriaBuilder.or(
                                        criteriaBuilder.like(root.get(UserEntity_.username), convertKeyword(keyword)),
                                        criteriaBuilder.like(root.get(UserEntity_.email), convertKeyword(keyword)))))
                        .orderBy(criteriaBuilder.asc(root)));

        getAllQuery.setMaxResults(nRow);
        getAllQuery.setFirstResult(nRow * (pageNumber - 1));

        return getAllQuery.getResultList();
    }
}

// Node: repos/cloned_ms_repos/saigonparking/service/user-service/src/main/java/com/bht/saigonparking/service/user/repository/custom/impl/UserRepositoryCustomImpl.java:UserRepositoryCustomImpl.<init>
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

package com.bht.saigonparking.service.booking.mapper;

import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

import javax.persistence.Tuple;
import javax.validation.constraints.NotNull;

import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.Named;
import org.mapstruct.NullValueMappingStrategy;
import org.springframework.data.util.Pair;
import org.springframework.stereotype.Component;

import com.bht.saigonparking.api.grpc.booking.Booking;
import com.bht.saigonparking.api.grpc.booking.BookingDetail;
import com.bht.saigonparking.api.grpc.booking.BookingHistory;
import com.bht.saigonparking.api.grpc.booking.BookingRating;
import com.bht.saigonparking.api.grpc.booking.CreateBookingRequest;
import com.bht.saigonparking.api.grpc.booking.ParkingLotBookingAndRatingStatistic;
import com.bht.saigonparking.api.grpc.booking.UpdateBookingStatusRequest;
import com.bht.saigonparking.service.booking.configuration.AppConfiguration;
import com.bht.saigonparking.service.booking.entity.BookingEntity;
import com.bht.saigonparking.service.booking.entity.BookingHistoryEntity;
import com.bht.saigonparking.service.booking.entity.BookingRatingEntity;
import com.bht.saigonparking.service.booking.entity.BookingStatisticEntity;

/**
 *
 * @author bht
 */
@Component
@SuppressWarnings("UnmappedTargetProperties")
@Mapper(componentModel = "spring", implementationPackage = AppConfiguration.BASE_PACKAGE + ".mapper.impl",
        nullValueMappingStrategy = NullValueMappingStrategy.RETURN_DEFAULT,
        uses = {EnumMapper.class, CustomizedMapper.class})
public interface BookingMapper {

    @Named("toBookingFromMapEntry")
    @Mapping(target = "id", source = "key.uuid", qualifiedByName = "toUUIDString", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    @Mapping(target = "parkingLotId", source = "key.parkingLotId", defaultExpression = "java(customizedMapper.DEFAULT_LONG_VALUE)")
    @Mapping(target = "parkingLotName", source = "value", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    @Mapping(target = "customerId", source = "key.customerId", defaultExpression = "java(customizedMapper.DEFAULT_LONG_VALUE)")
    @Mapping(target = "licensePlate", source = "key.customerLicensePlate", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    @Mapping(target = "createdAt", source = "key.createdAt", qualifiedByName = "toTimestampString", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    @Mapping(target = "isFinished", source = "key.isFinished", defaultExpression = "java(customizedMapper.DEFAULT_BOOL_VALUE)")
    @Mapping(target = "isRated", source = "key.isRated", defaultExpression = "java(customizedMapper.DEFAULT_BOOL_VALUE)")
    @Mapping(target = "latestStatus", source = "key.bookingStatusEntity", qualifiedByName = "toBookingStatus")
    Booking toBooking(@NotNull Map.Entry<BookingEntity, String> bookingEntityParkingLotNameEntry);

    @Named("toBooking")
    @Mapping(target = "id", source = "uuid", qualifiedByName = "toUUIDString", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    @Mapping(target = "parkingLotId", source = "parkingLotId", defaultExpression = "java(customizedMapper.DEFAULT_LONG_VALUE)")
    @Mapping(target = "parkingLotName", source = "parkingLotId", qualifiedByName = "toParkingLotName", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    @Mapping(target = "customerId", source = "customerId", defaultExpression = "java(customizedMapper.DEFAULT_LONG_VALUE)")
    @Mapping(target = "licensePlate", source = "customerLicensePlate", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    @Mapping(target = "createdAt", source = "createdAt", qualifiedByName = "toTimestampString", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    @Mapping(target = "isFinished", source = "isFinished", defaultExpression = "java(customizedMapper.DEFAULT_BOOL_VALUE)")
    @Mapping(target = "isRated", source = "isRated", defaultExpression = "java(customizedMapper.DEFAULT_BOOL_VALUE)")
    @Mapping(target = "latestStatus", source = "bookingStatusEntity", qualifiedByName = "toBookingStatus")
    Booking toBooking(@NotNull BookingEntity bookingEntity);

    @Named("toBookingEntity")
    @Mapping(target = "parkingLotId", source = "parkingLotId", defaultExpression = "java(customizedMapper.DEFAULT_LONG_VALUE)")
    @Mapping(target = "customerId", source = "customerId", defaultExpression = "java(customizedMapper.DEFAULT_LONG_VALUE)")
    @Mapping(target = "customerLicensePlate", source = "licensePlate", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    @Mapping(target = "bookingStatusEntity", expression = "java(enumMapper.getDefaultBookingStatusEntity())")
    @Mapping(target = "isFinished", constant = "false")
    @Mapping(target = "isRated", constant = "false")
    @Mapping(target = "version", constant = "1L")
    @Mapping(target = "uuid", expression = "java(customizedMapper.generateUUID())")
    @Mapping(target = "id", ignore = true)
    BookingEntity toBookingEntity(@NotNull CreateBookingRequest bookingRequest);

    @Named("toBookingHistory")
    @Mapping(target = "id", source = "id", defaultExpression = "java(customizedMapper.DEFAULT_LONG_VALUE)")
    @Mapping(target = "status", source = "bookingStatusEntity", qualifiedByName = "toBookingStatus")
    @Mapping(target = "timestamp", source = "lastUpdated", qualifiedByName = "toTimestampString", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    @Mapping(target = "note", source = "note", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    BookingHistory toBookingHistory(@NotNull BookingHistoryEntity bookingHistoryEntity);

    @Named("toBookingHistoryEntity")
    @Mapping(target = "bookingEntity", ignore = true)
    @Mapping(target = "bookingStatusEntity", source = "status", qualifiedByName = "toBookingStatusEntity")
    @Mapping(target = "note", source = "note", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    @Mapping(target = "lastUpdated", ignore = true)
    @Mapping(target = "version", constant = "1L")
    @Mapping(target = "id", ignore = true)
    BookingHistoryEntity toBookingHistoryEntity(@NotNull UpdateBookingStatusRequest updateBookingStatusRequest);

    @Named("toBookingDetail")
    default BookingDetail toBookingDetail(@NotNull BookingEntity bookingEntity) {
        return BookingDetail.newBuilder()
                .setBooking(toBooking(bookingEntity))
                .addAllHistory(toBookingHistoryList(bookingEntity.getBookingHistoryEntitySet()))
                .build();
    }

    @Named("toBookingList")
    default List<Booking> toBookingList(@NotNull Map<BookingEntity, String> bookingEntityParkingLotNameMap) {
        return bookingEntityParkingLotNameMap.entrySet().stream()
                .sorted(BookingEntity.SORT_BY_CREATED_AT_THEN_BY_BOOKING_ID)
                .map(this::toBooking)
                .collect(Collectors.toList());
    }

    @Named("toBookingHistoryList")
    default List<BookingHistory> toBookingHistoryList(@NotNull Set<BookingHistoryEntity> bookingHistoryEntitySet) {
        return bookingHistoryEntitySet.stream()
                .sorted(BookingHistoryEntity.SORT_BY_LAST_UPDATED_THEN_BY_ID)
                .map(this::toBookingHistory)
                .collect(Collectors.toList());
    }

    @Named("toParkingLotBookingAndRatingStatistic")
    @Mapping(target = "parkingLotId", source = "parkingLotId", defaultExpression = "java(customizedMapper.DEFAULT_LONG_VALUE)")
    @Mapping(target = "NBooking", source = "NBooking", defaultExpression = "java(customizedMapper.DEFAULT_LONG_VALUE)")
    @Mapping(target = "NRating", source = "NRating", defaultExpression = "java(customizedMapper.DEFAULT_LONG_VALUE)")
    @Mapping(target = "ratingAverage", source = "ratingAverage", defaultExpression = "java(customizedMapper.DEFAULT_DOUBLE_VALUE)")
    ParkingLotBookingAndRatingStatistic toParkingLotBookingAndRatingStatistic(@NotNull BookingStatisticEntity bookingStatisticEntity);

    @Named("toBookingRatingFromTupleEntry")
    @Mapping(target = "bookingId", expression = "java(bookingRatingTupleEntry.getKey().get(0, java.util.UUID.class).toString())")
    @Mapping(target = "username", source = "value", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    @Mapping(target = "rating", expression = "java(bookingRatingTupleEntry.getKey().get(3, Short.class).intValue())")
    @Mapping(target = "comment", expression = "java(bookingRatingTupleEntry.getKey().get(4, String.class))")
    @Mapping(target = "lastUpdated", expression = "java(customizedMapper.toTimestampString(bookingRatingTupleEntry.getKey().get(5, java.sql.Timestamp.class)))")
    BookingRating toBookingRating(@NotNull Map.Entry<Tuple, String> bookingRatingTupleEntry);

    @Named("toBookingRating")
    @Mapping(target = "bookingId", source = "first.bookingEntity.uuid", qualifiedByName = "toUUIDString", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    @Mapping(target = "rating", source = "first.rating", defaultExpression = "java(customizedMapper.DEFAULT_SHORT_VALUE)")
    @Mapping(target = "comment", source = "first.comment", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    @Mapping(target = "lastUpdated", source = "first.lastUpdated", qualifiedByName = "toTimestampString", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    @Mapping(target = "username", source = "second", defaultExpression = "java(customizedMapper.DEFAULT_STRING_VALUE)")
    BookingRating toBookingRating(@NotNull Pair<BookingRatingEntity, String> bookingRatingEntityUsernamePair);

    @Named("toParkingLotBookingAndRatingStatisticList")
    default List<ParkingLotBookingAndRatingStatistic> toParkingLotBookingAndRatingStatisticList(@NotNull List<BookingStatisticEntity> bookingStatisticEntityList) {
        return bookingStatisticEntityList.stream().map(this::toParkingLotBookingAndRatingStatistic).collect(Collectors.toList());
    }

    @Named("toParkingLotRatingListFromTupleMap")
    default List<BookingRating> toBookingRatingList(@NotNull Map<Tuple, String> bookingRatingTupleUsernameMap) {
        return bookingRatingTupleUsernameMap.entrySet().stream().map(this::toBookingRating).collect(Collectors.toList());
    }
}

// Node: repos/cloned_ms_repos/saigonparking/service/booking-service/src/main/java/com/bht/saigonparking/service/booking/mapper/BookingMapper.java:BookingMapper.<init>
// Node: toBooking
// Node: getDefaultBookingStatusEntity
// Node: toBookingEntity
// Node: toBookingHistory
// Node: toBookingHistoryEntity
// Node: toBookingDetail
// Node: setBooking
// Node: addAllHistory
// Node: toBookingHistoryList
// Node: getBookingHistoryEntitySet
// Node: sorted
// Node: toParkingLotBookingAndRatingStatistic
// Node: intValue
// Node: toBookingRating
// Node: toParkingLotBookingAndRatingStatisticList
// Node: toBookingRatingList
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

// Node: initBookingStatusValueMap
// Node: toBookingStatus
// Node: toBookingStatusValue
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

// Node: toUUIDString
// Node: toParkingLotName
// Node: getParkingLotNameMap
package com.bht.saigonparking.service.booking.repository.custom.impl;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import javax.persistence.Tuple;
import javax.validation.constraints.Max;
import javax.validation.constraints.NotNull;

import org.hibernate.validator.constraints.Range;
import org.springframework.stereotype.Repository;

import com.bht.saigonparking.common.base.BaseRepositoryCustom;
import com.bht.saigonparking.service.booking.repository.custom.BookingRatingRepositoryCustom;

/**
 *
 * @author bht
 */
@Repository
public class BookingRatingRepositoryCustomImpl extends BaseRepositoryCustom implements BookingRatingRepositoryCustom {

    @Override
    public Long countAllRatingsOfParkingLot(@NotNull Long parkingLotId) {

        String countAllQuery = "SELECT COUNT(R.id) " +
                "FROM BookingRatingEntity R JOIN R.bookingEntity B " +
                "WHERE B.parkingLotId = :parkingLotId ";

        return entityManager.createQuery(countAllQuery, Long.class)
                .setParameter("parkingLotId", parkingLotId)
                .getSingleResult();
    }

    @Override
    public Long countAllRatingsOfParkingLot(@NotNull Long parkingLotId, @NotNull @Range(min = 1L, max = 5L) Integer rating) {

        String countAllQuery = "SELECT COUNT(R.id) " +
                "FROM BookingRatingEntity R JOIN R.bookingEntity B " +
                "WHERE B.parkingLotId = :parkingLotId AND R.rating = :rating ";

        return entityManager.createQuery(countAllQuery, Long.class)
                .setParameter("parkingLotId", parkingLotId)
                .setParameter("rating", rating.shortValue())
                .getSingleResult();
    }

    @Override
    public List<Tuple> getAllRatingsOfParkingLot(@NotNull Long parkingLotId,
                                                 boolean sortLastUpdatedAsc,
                                                 @NotNull @Max(20L) Integer nRow,
                                                 @NotNull Integer pageNumber) {

        String getAllQuery = "SELECT B.uuid, B.parkingLotId, B.customerId, R.rating, R.comment, R.lastUpdated " +
                "FROM BookingRatingEntity R JOIN R.bookingEntity B " +
                "WHERE B.parkingLotId = :parkingLotId " +
                "ORDER BY R.lastUpdated " + (sortLastUpdatedAsc ? " ASC " : " DESC ");

        return entityManager.createQuery(getAllQuery, Tuple.class)
                .setParameter("parkingLotId", parkingLotId)
                .setMaxResults(nRow)
                .setFirstResult(nRow * (pageNumber - 1))
                .getResultList();
    }

    @Override
    public List<Tuple> getAllRatingsOfParkingLot(@NotNull Long parkingLotId,
                                                 @NotNull @Range(min = 1L, max = 5L) Integer rating,
                                                 boolean sortLastUpdatedAsc,
                                                 @NotNull @Max(20L) Integer nRow,
                                                 @NotNull Integer pageNumber) {

        String getAllQuery = "SELECT B.uuid, B.parkingLotId, B.customerId, R.rating, R.comment, R.lastUpdated " +
                "FROM BookingRatingEntity R JOIN R.bookingEntity B " +
                "WHERE B.parkingLotId = :parkingLotId AND R.rating = :rating " +
                "ORDER BY R.lastUpdated " + (sortLastUpdatedAsc ? " ASC " : " DESC ");

        return entityManager.createQuery(getAllQuery, Tuple.class)
                .setParameter("parkingLotId", parkingLotId)
                .setParameter("rating", rating.shortValue())
                .setMaxResults(nRow)
                .setFirstResult(nRow * (pageNumber - 1))
                .getResultList();
    }

    @Override
    public Map<Integer, Long> getParkingLotRatingCountGroupByRating(@NotNull Long parkingLotId) {

        String getCountGroupByQuery = "SELECT R.rating, COUNT(R.id) " +
                "FROM BookingRatingEntity R JOIN R.bookingEntity B " +
                "WHERE B.parkingLotId = :parkingLotId " +
                "GROUP BY R.rating ";

        return entityManager.createQuery(getCountGroupByQuery, Tuple.class)
                .setParameter("parkingLotId", parkingLotId)
                .getResultList().stream()
                .collect(Collectors.toMap(record -> record.get(0, Short.class).intValue(), record -> record.get(1, Long.class)));
    }
}

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

// Node: getHeaders
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

// Node: getAccessTokenFromUri
// Node: getURI
// Node: substring
// Node: lastIndexOf
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

package com.bht.saigonparking.service.contact.service;

import java.util.Map;

import javax.validation.constraints.NotNull;

import com.bht.saigonparking.common.auth.SaigonParkingTokenBody;

/**
 *
 * @author bht
 */
public interface HandshakeService {

    /**
     * if JWT token is successfully parsed, it means authentication is success
     * after authentication succeeded, this method will be run
     * and return a new attribute map for re-assign purpose
     *
     * @param tokenBody all fields parsed from JWT
     * @param mustConsumeFromQueue must register a queue and listen to it or not
     * @return Map of session attributes
     */
    Map<String, Object> postAuthentication(@NotNull SaigonParkingTokenBody tokenBody, boolean mustConsumeFromQueue);
}

// Node: repos/cloned_ms_repos/saigonparking/service/contact-service/src/main/java/com/bht/saigonparking/service/contact/service/HandshakeService.java:HandshakeService.<init>
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

// Node: remove
// Node: removeQueueNames
package com.bht.saigonparking.emulator;

import static com.bht.saigonparking.api.grpc.contact.SaigonParkingMessage.Classification.CUSTOMER_MESSAGE;
import static com.bht.saigonparking.api.grpc.contact.SaigonParkingMessage.Classification.PARKING_LOT_MESSAGE;
import static com.bht.saigonparking.api.grpc.contact.SaigonParkingMessage.Type.BOOKING_REQUEST;
import static com.bht.saigonparking.api.grpc.contact.SaigonParkingMessage.Type.TEXT_MESSAGE;

import java.io.IOException;
import java.net.URI;
import java.util.Collections;
import java.util.concurrent.ExecutionException;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.builder.SpringApplicationBuilder;
import org.springframework.boot.web.servlet.support.SpringBootServletInitializer;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.web.socket.WebSocketHttpHeaders;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.client.WebSocketClient;
import org.springframework.web.socket.client.standard.StandardWebSocketClient;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import com.bht.saigonparking.api.grpc.auth.AuthServiceGrpc;
import com.bht.saigonparking.api.grpc.auth.ValidateRequest;
import com.bht.saigonparking.api.grpc.contact.BookingRequestContent;
import com.bht.saigonparking.api.grpc.contact.SaigonParkingMessage;
import com.bht.saigonparking.api.grpc.contact.TextMessageContent;
import com.bht.saigonparking.api.grpc.user.UserRole;
import com.bht.saigonparking.emulator.configuration.SpringApplicationContext;
import com.bht.saigonparking.emulator.handler.WebSocketHandler;
import com.neovisionaries.ws.client.WebSocket;
import com.neovisionaries.ws.client.WebSocketAdapter;
import com.neovisionaries.ws.client.WebSocketException;
import com.neovisionaries.ws.client.WebSocketFactory;

import lombok.extern.log4j.Log4j2;

/**
 *
 * @author bht
 */
@Log4j2
@EnableScheduling
@SpringBootApplication
@SuppressWarnings("all")
public class Emulator extends SpringBootServletInitializer {

    private static final String SAMPLE_TOKEN_CUSTOMER = "eyJhbGciOiJIUzUxMiJ9.eyJqdGkiOiIyOTIwMzczOTE3OTY1NDQ5Mzg4QDE1OTM3ODQwNzY4MjYiLCJpc3MiOiJ3d3cuc2FpZ29ucGFya2luZy53dGYiLCJyb2xlIjoiQ1VTVE9NRVIiLCJmYWMiOjE1OCwiY2xhc3NpZmljYXRpb24iOiJBQ0NFU1NfVE9LRU4iLCJzdWIiOiIyOTIwMzczOTE3OTY1NDQ5Mzg4IiwiaWF0IjoxNTkzNzg0MDc2LCJleHAiOjIzMTk1NDQwNzZ9.Hf0iUOFva2ToExAZXi6jcIzMpWBbideNGOnzHLtpu1uJs3J9HQF8CZrxKKMCbK0rQ-5j3yg_Ovm8flqMSXZRnA";
    private static final String SAMPLE_TOKEN_EMPLOYEE = "eyJhbGciOiJIUzUxMiJ9.eyJqdGkiOiIyNTAzNDU2NTMyNTg4NDQ0ODcyQDE1OTM3ODQyNzc2ODciLCJpc3MiOiJ3d3cuc2FpZ29ucGFya2luZy53dGYiLCJyb2xlIjoiUEFSS0lOR19MT1RfRU1QTE9ZRUUiLCJmYWMiOjgwNSwiY2xhc3NpZmljYXRpb24iOiJBQ0NFU1NfVE9LRU4iLCJzdWIiOiIyNTAzNDU2NTMyNTg4NDQ0ODcyIiwiaWF0IjoxNTkzNzg0Mjc3LCJleHAiOjIzMTk1NDQyNzd9.s2uE7fHIiAhjgsO5Oz9Gl4fIOXdC2Va8NjHS06x9q5V7laBCdOHF9CyaCaP34fZdLGxRj4xxqGWOS4hJIGDrPg";

    private static final URI WEB_SOCKET_LOCAL_URI = URI.create("ws://localhost:8000/contact");
    private static final URI WEB_SOCKET_WEB_LOCAL_URI = URI.create("ws://localhost:8000/contact/web?token=" + SAMPLE_TOKEN_CUSTOMER);

    @Override
    protected SpringApplicationBuilder configure(SpringApplicationBuilder builder) {
        return builder.sources(Emulator.class);
    }

    public static void main(String[] args) throws ExecutionException, InterruptedException, IOException, WebSocketException {
        SpringApplication.run(Emulator.class, args);
        runTest();
    }

    private static void runTest() throws ExecutionException, InterruptedException, IOException, WebSocketException {
//        testAuthWithWebSocketUri();
//        testAuthWithWebSocketWebUri();
//        testNewSocketLibrary();

//        Thread.sleep(5000);
//
//        ContactServiceGrpc.ContactServiceBlockingStub contactServiceBlockingStub =
//                SpringApplicationContext.getBean(ContactServiceGrpc.ContactServiceBlockingStub.class);
//
//        System.out.println(contactServiceBlockingStub.checkUserOnlineByUserId(Int64Value.of(4)).getValue());
//        System.out.println(contactServiceBlockingStub.checkUserOnlineByUserId(Int64Value.of(84)).getValue());
//        System.out.println(contactServiceBlockingStub.checkParkingLotOnlineByParkingLotId(Int64Value.of(72)).getValue());
//
//        Thread.sleep(86400000);

//        System.out.println(SpringApplicationContext.getBean(BookingServiceGrpc.BookingServiceBlockingStub.class)
//                .createBooking(CreateBookingRequest.newBuilder()
//                        .setCustomerId(4)
//                        .setParkingLotId(1)
//                        .setLicensePlate("59H1-762.17")
//                        .build())
//                .getValue());

//        SpringApplicationContext.getBean(BookingServiceGrpc.BookingServiceBlockingStub.class)
//                .updateBookingStatus(UpdateBookingStatusRequest.newBuilder()
//                        .setBookingId(1)
//                        .setStatus(BookingStatus.REJECTED)
//                        .setTimestamp(new Timestamp(System.currentTimeMillis()).toString())
//                        .build());

//        System.out.println(SpringApplicationContext.getBean(BookingServiceGrpc.BookingServiceBlockingStub.class)
//                .createBooking(CreateBookingRequest.newBuilder()
//                        .setCustomerId(4)
//                        .setParkingLotId(4)
//                        .setLicensePlate("59H1-762.17")
//                        .build()));

//        SpringApplicationContext.getBean(ParkingLotServiceGrpc.ParkingLotServiceBlockingStub.class)
//                .createNewParkingLot(ParkingLot.newBuilder()
//                        .setType(ParkingLotType.BUILDING)
//                        .setLatitude(10.762622)
//                        .setLongitude(106.660172)
//                        .setOpeningHour("00:00:00")
//                        .setClosingHour("20:00:00")
//                        .setAvailableSlot(100)
//                        .setTotalSlot(100)
//                        .setInformation(ParkingLotInformation.newBuilder()
//                                .setName("BX Test")
//                                .setAddress("227 Nguyen Van Cu")
//                                .setPhone("0123456789")
//                                .build())
//                        .build())
//                .getValue();

        System.out.println(SpringApplicationContext.getBean(AuthServiceGrpc.AuthServiceBlockingStub.class)
                .validateUser(ValidateRequest.newBuilder()
                        .setUsername("htbinh")
                        .setPassword("htbinh789")
                        .setRole(UserRole.CUSTOMER)
                        .build()));
    }

    private static void testAuthWithWebSocketUri() throws ExecutionException, InterruptedException, IOException {
        TextWebSocketHandler webSocketHandler = SpringApplicationContext.getBean(WebSocketHandler.class);
        WebSocketHttpHeaders webSocketHttpHeaders = new WebSocketHttpHeaders();
        webSocketHttpHeaders.put("Authorization", Collections.singletonList(SAMPLE_TOKEN_CUSTOMER));

        WebSocketClient webSocketClient = new StandardWebSocketClient();
        WebSocketSession webSocketSession = webSocketClient
                .doHandshake(webSocketHandler, webSocketHttpHeaders, WEB_SOCKET_LOCAL_URI).get();

        webSocketSession.close();
    }

    private static void testAuthWithWebSocketWebUri() throws ExecutionException, InterruptedException, IOException {
        TextWebSocketHandler webSocketHandler = SpringApplicationContext.getBean(WebSocketHandler.class);
        WebSocketHttpHeaders webSocketHttpHeaders = new WebSocketHttpHeaders();

        WebSocketClient webSocketClient = new StandardWebSocketClient();
        WebSocketSession webSocketSession = webSocketClient
                .doHandshake(webSocketHandler, webSocketHttpHeaders, WEB_SOCKET_WEB_LOCAL_URI).get();

        webSocketSession.close();
    }

    private static void testNewSocketLibrary() throws IOException, WebSocketException, InterruptedException {
//        testSocketAsEmployee();
        testSocketAsCustomer();
    }

    private static void testSocketAsCustomer() throws IOException, WebSocketException, InterruptedException {
        WebSocketFactory webSocketFactory = new WebSocketFactory();
        WebSocket webSocket = webSocketFactory.createSocket(WEB_SOCKET_LOCAL_URI, 86400000);

        webSocket.addHeader("Authorization", SAMPLE_TOKEN_CUSTOMER);

        webSocket.addListener(new WebSocketAdapter() {
            @Override
            public void onBinaryMessage(WebSocket websocket, byte[] binary) throws Exception {
                SaigonParkingMessage saigonParkingMessage = SaigonParkingMessage.parseFrom(binary);
                System.out.println(saigonParkingMessage);
                System.out.println(BookingRequestContent.parseFrom(saigonParkingMessage.getContent()));
            }
        });

        webSocket.connect();
        Thread.sleep(2000);

        TextMessageContent customerTextMessageContent = TextMessageContent.newBuilder()
                .setSender("htbinh")
                .setMessage("Hello parkinglot")
                .build();

        BookingRequestContent bookingRequestContent = BookingRequestContent.newBuilder()
                .setAmountOfParkingHour(5)
                .setCustomerName("htbinh")
                .setCustomerLicense("54L6-2908")
                .setParkingLotId(72)
                .build();

        SaigonParkingMessage textMessage = SaigonParkingMessage.newBuilder()
                .setClassification(CUSTOMER_MESSAGE)
                .setType(BOOKING_REQUEST)
                .setSenderId(4)
                .setReceiverId(72)
                .setContent(bookingRequestContent.toByteString())
                .build();

        webSocket.sendBinary(textMessage.toByteArray());
        //webSocket.disconnect();
    }

    private static void testSocketAsEmployee() throws IOException, WebSocketException, InterruptedException {
        WebSocketFactory webSocketFactory = new WebSocketFactory();
        WebSocket webSocket = webSocketFactory.createSocket(WEB_SOCKET_LOCAL_URI, 86400000);

        webSocket.addHeader("Authorization", SAMPLE_TOKEN_EMPLOYEE);

        webSocket.addListener(new WebSocketAdapter() {
            @Override
            public void onBinaryMessage(WebSocket websocket, byte[] binary) throws Exception {
                SaigonParkingMessage saigonParkingMessage = SaigonParkingMessage.parseFrom(binary);
                System.out.println(saigonParkingMessage);
            }
        });

        webSocket.connect();
        Thread.sleep(2000);

        TextMessageContent parkingLotTextMessageContent = TextMessageContent.newBuilder()
                .setSender("parkinglot")
                .setMessage("Hello htbinh")
                .build();

        SaigonParkingMessage textMessage = SaigonParkingMessage.newBuilder()
                .setClassification(PARKING_LOT_MESSAGE)
                .setType(TEXT_MESSAGE)
                .setSenderId(84)
                .setReceiverId(4)
                .setContent(parkingLotTextMessageContent.toByteString())
                .build();

        webSocket.sendBinary(textMessage.toByteArray());
        //webSocket.disconnect();
    }
}

// Node: repos/cloned_ms_repos/saigonparking/emulator/src/main/java/com/bht/saigonparking/emulator/Emulator.java:Emulator.<init>
package com.bht.saigonparking.emulator.configuration;

import java.lang.reflect.Proxy;

import org.apache.logging.log4j.Level;
import org.springframework.beans.factory.config.DestructionAwareBeanPostProcessor;
import org.springframework.lang.NonNull;
import org.springframework.stereotype.Component;

import com.bht.saigonparking.emulator.base.BaseBean;
import com.bht.saigonparking.emulator.util.LoggingUtil;

/**
 *
 * @author bht
 */
@Component
public final class SpringBeanLifeCycle implements BaseBean, DestructionAwareBeanPostProcessor {


    @Override
    public void initialize() {
        BaseBean.super.initialize();
        LoggingUtil.log(Level.INFO, "SPRING", "BeanCreation", "springBeanLifeCycle");
    }


    @Override
    public void destroy() {
        BaseBean.super.destroy();
        LoggingUtil.log(Level.INFO, "SPRING", "BeanDestruction", "springBeanLifeCycle");
    }


    @Override
    public Object postProcessBeforeInitialization(@NonNull Object bean, @NonNull String beanName) {
        if (!(bean instanceof Proxy) && bean.getClass().getPackage().getName().startsWith(AppConfiguration.BASE_PACKAGE_SERVER)) {
            LoggingUtil.log(Level.INFO, "SPRING", "BeanCreation", beanName);
        }
        return DestructionAwareBeanPostProcessor.super.postProcessBeforeInitialization(bean, beanName);
    }


    @Override
    public void postProcessBeforeDestruction(@NonNull Object bean, @NonNull String beanName) {
        if (!(bean instanceof Proxy) && bean.getClass().getPackage().getName().startsWith(AppConfiguration.BASE_PACKAGE_SERVER)) {
            LoggingUtil.log(Level.INFO, "SPRING", "BeanDestruction", beanName);
        }
    }
}

package com.bht.saigonparking.emulator.base;

import javax.annotation.PostConstruct;
import javax.annotation.PreDestroy;

/**
 *
 * @author bht
 */
public interface BaseBean {


    @PostConstruct
    default void initialize() {
    }

    @PreDestroy
    default void destroy() {
    }
}

