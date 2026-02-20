// Cluster 10

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

// Node: PermissionDeniedException
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

// Node: convertKeyword
// Node: now
// Node: from
// Node: getId
package com.bht.saigonparking.service.parkinglot.repository.custom;

import java.util.List;

import javax.persistence.Tuple;
import javax.validation.constraints.Max;
import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;

import com.bht.saigonparking.service.parkinglot.entity.ParkingLotEntity;
import com.bht.saigonparking.service.parkinglot.entity.ParkingLotTypeEntity;

/**
 *
 * @author bht
 */
public interface ParkingLotRepositoryCustom {

    List<Tuple> countAllParkingLotGroupByType();

    Long countAll();

    Long countAll(boolean isAvailable);

    Long countAll(@NotEmpty String keyword);

    Long countAll(@NotNull ParkingLotTypeEntity parkingLotTypeEntity);

    Long countAll(@NotEmpty String keyword, boolean isAvailable);

    Long countAll(@NotNull ParkingLotTypeEntity parkingLotTypeEntity, boolean isAvailable);

    Long countAll(@NotEmpty String keyword, @NotNull ParkingLotTypeEntity parkingLotTypeEntity);

    Long countAll(@NotEmpty String keyword, @NotNull ParkingLotTypeEntity parkingLotTypeEntity, boolean isAvailable);

    List<ParkingLotEntity> getAll(@NotNull @Max(20L) Integer nRow,
                                  @NotNull Integer pageNumber);

    List<ParkingLotEntity> getAll(@NotNull @Max(20L) Integer nRow,
                                  @NotNull Integer pageNumber,
                                  boolean isAvailable);

    List<ParkingLotEntity> getAll(@NotNull @Max(20L) Integer nRow,
                                  @NotNull Integer pageNumber,
                                  @NotEmpty String keyword);

    List<ParkingLotEntity> getAll(@NotNull @Max(20L) Integer nRow,
                                  @NotNull Integer pageNumber,
                                  @NotNull ParkingLotTypeEntity parkingLotTypeEntity);

    List<ParkingLotEntity> getAll(@NotNull @Max(20L) Integer nRow,
                                  @NotNull Integer pageNumber,
                                  @NotEmpty String keyword,
                                  boolean isAvailable);

    List<ParkingLotEntity> getAll(@NotNull @Max(20L) Integer nRow,
                                  @NotNull Integer pageNumber,
                                  @NotNull ParkingLotTypeEntity parkingLotTypeEntity,
                                  boolean isAvailable);

    List<ParkingLotEntity> getAll(@NotNull @Max(20L) Integer nRow,
                                  @NotNull Integer pageNumber,
                                  @NotEmpty String keyword,
                                  @NotNull ParkingLotTypeEntity parkingLotTypeEntity);

    List<ParkingLotEntity> getAll(@NotNull @Max(20L) Integer nRow,
                                  @NotNull Integer pageNumber,
                                  @NotEmpty String keyword,
                                  @NotNull ParkingLotTypeEntity parkingLotTypeEntity,
                                  boolean isAvailable);
}

// Node: repos/cloned_ms_repos/saigonparking/service/parkinglot-service/src/main/java/com/bht/saigonparking/service/parkinglot/repository/custom/ParkingLotRepositoryCustom.java:ParkingLotRepositoryCustom.<init>
// Node: countAllParkingLotGroupByType
// Node: countAll
// Node: getAll
// Node: Max
package com.bht.saigonparking.service.parkinglot.repository.custom.impl;

import javax.validation.constraints.NotNull;

import org.springframework.stereotype.Repository;

import com.bht.saigonparking.common.base.BaseRepositoryCustom;
import com.bht.saigonparking.service.parkinglot.repository.custom.ParkingLotEmployeeRepositoryCustom;

/**
 *
 * @author bht
 */
@Repository
public class ParkingLotEmployeeRepositoryCustomImpl extends BaseRepositoryCustom implements ParkingLotEmployeeRepositoryCustom {

    @Override
    public Long getParkingLotIdByParkingLotEmployeeId(@NotNull Long parkingLotEmployeeId) {

        String query = "SELECT PLE.parkingLotEntity.id " +
                "FROM ParkingLotEmployeeEntity PLE " +
                "WHERE PLE.userId = :parkingLotEmployeeId";

        return entityManager.createQuery(query, Long.class)
                .setParameter("parkingLotEmployeeId", parkingLotEmployeeId)
                .getSingleResult();
    }
}

// Node: createQuery
// Node: setParameter
// Node: getSingleResult
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

// Node: COUNT
// Node: getResultList
// Node: select
// Node: count
// Node: where
// Node: and
// Node: equal
// Node: lessThanOrEqualTo
// Node: greaterThanOrEqualTo
// Node: or
// Node: greaterThan
// Node: currentTime
// Node: lessThan
// Node: join
// Node: like
// Node: fetch
// Node: orderBy
// Node: asc
// Node: setMaxResults
// Node: setFirstResult
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

// Node: emptyList
package com.bht.saigonparking.service.user.repository.custom;

import java.util.List;

import javax.persistence.Tuple;
import javax.validation.constraints.Max;
import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;

import com.bht.saigonparking.service.user.entity.UserEntity;
import com.bht.saigonparking.service.user.entity.UserRoleEntity;

/**
 *
 * @author bht
 */
public interface UserRepositoryCustom {

    List<Tuple> countAllUserGroupByRole();

    Long countAll();

    Long countAll(@NotNull Boolean isActivated);

    Long countAll(@NotEmpty String keyword);

    Long countAll(@NotNull UserRoleEntity userRoleEntity);

    Long countAll(@NotEmpty String keyword, @NotNull Boolean isActivated);

    Long countAll(@NotNull UserRoleEntity userRoleEntity, @NotNull Boolean isActivated);

    Long countAll(@NotEmpty String keyword, @NotNull UserRoleEntity userRoleEntity);

    Long countAll(@NotEmpty String keyword, @NotNull UserRoleEntity userRoleEntity, @NotNull Boolean isActivated);

    List<UserEntity> getAll(@NotNull @Max(20L) Integer nRow,
                            @NotNull Integer pageNumber);

    List<UserEntity> getAll(@NotNull @Max(20L) Integer nRow,
                            @NotNull Integer pageNumber,
                            @NotNull Boolean isActivated);

    List<UserEntity> getAll(@NotNull @Max(20L) Integer nRow,
                            @NotNull Integer pageNumber,
                            @NotEmpty String keyword);

    List<UserEntity> getAll(@NotNull @Max(20L) Integer nRow,
                            @NotNull Integer pageNumber,
                            @NotNull UserRoleEntity userRoleEntity);

    List<UserEntity> getAll(@NotNull @Max(20L) Integer nRow,
                            @NotNull Integer pageNumber,
                            @NotEmpty String keyword,
                            @NotNull Boolean isActivated);

    List<UserEntity> getAll(@NotNull @Max(20L) Integer nRow,
                            @NotNull Integer pageNumber,
                            @NotNull UserRoleEntity userRoleEntity,
                            @NotNull Boolean isActivated);

    List<UserEntity> getAll(@NotNull @Max(20L) Integer nRow,
                            @NotNull Integer pageNumber,
                            @NotEmpty String keyword,
                            @NotNull UserRoleEntity userRoleEntity);

    List<UserEntity> getAll(@NotNull @Max(20L) Integer nRow,
                            @NotNull Integer pageNumber,
                            @NotEmpty String keyword,
                            @NotNull UserRoleEntity userRoleEntity,
                            @NotNull Boolean isActivated);
}

// Node: repos/cloned_ms_repos/saigonparking/service/user-service/src/main/java/com/bht/saigonparking/service/user/repository/custom/UserRepositoryCustom.java:UserRepositoryCustom.<init>
// Node: countAllUserGroupByRole
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

// Node: mapToUsernameMap
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

package com.bht.saigonparking.service.booking.repository.custom;

import java.util.List;
import java.util.Map;

import javax.persistence.Tuple;
import javax.validation.constraints.Max;
import javax.validation.constraints.NotNull;

import org.hibernate.validator.constraints.Range;

/**
 *
 * @author bht
 */
public interface BookingRatingRepositoryCustom {

    Long countAllRatingsOfParkingLot(@NotNull Long parkingLotId);

    Long countAllRatingsOfParkingLot(@NotNull Long parkingLotId,
                                     @NotNull @Range(min = 1L, max = 5L) Integer rating);

    List<Tuple> getAllRatingsOfParkingLot(@NotNull Long parkingLotId,
                                          boolean sortLastUpdatedAsc,
                                          @NotNull @Max(20L) Integer nRow,
                                          @NotNull Integer pageNumber);

    List<Tuple> getAllRatingsOfParkingLot(@NotNull Long parkingLotId,
                                          @NotNull @Range(min = 1L, max = 5L) Integer rating,
                                          boolean sortLastUpdatedAsc,
                                          @NotNull @Max(20L) Integer nRow,
                                          @NotNull Integer pageNumber);

    Map<Integer, Long> getParkingLotRatingCountGroupByRating(@NotNull Long parkingLotId);
}

// Node: repos/cloned_ms_repos/saigonparking/service/booking-service/src/main/java/com/bht/saigonparking/service/booking/repository/custom/BookingRatingRepositoryCustom.java:BookingRatingRepositoryCustom.<init>
// Node: countAllRatingsOfParkingLot
// Node: Range
// Node: getAllRatingsOfParkingLot
// Node: getParkingLotRatingCountGroupByRating
package com.bht.saigonparking.service.booking.repository.custom;

import java.util.List;
import java.util.Optional;

import javax.persistence.Tuple;
import javax.validation.constraints.NotNull;

import com.bht.saigonparking.service.booking.entity.BookingEntity;
import com.bht.saigonparking.service.booking.entity.BookingStatusEntity;

/**
 *
 * @author bht
 */
public interface BookingRepositoryCustom {

    List<Tuple> countAllBookingGroupByStatus();

    List<Tuple> countAllBookingOfParkingLotGroupByStatus(@NotNull Long parkingLotId);

    Long countAllBooking();

    Long countAllBooking(@NotNull BookingStatusEntity bookingStatusEntity);

    Long countAllBookingOfCustomer(@NotNull Long customerId);

    Long countAllBookingOfParkingLot(@NotNull Long parkingLotId);

    Long countAllBookingOfParkingLot(@NotNull Long parkingLotId,
                                     @NotNull BookingStatusEntity bookingStatusEntity);

    Long countAllOnGoingBookingOfParkingLot(@NotNull Long parkingLotId);

    List<BookingEntity> getAllBooking(@NotNull Integer nRow,
                                      @NotNull Integer pageNumber);

    List<BookingEntity> getAllBooking(@NotNull BookingStatusEntity bookingStatusEntity,
                                      @NotNull Integer nRow,
                                      @NotNull Integer pageNumber);

    List<BookingEntity> getAllBookingOfCustomer(@NotNull Long customerId,
                                                @NotNull Integer nRow,
                                                @NotNull Integer pageNumber);

    List<BookingEntity> getAllBookingOfParkingLot(@NotNull Long parkingLotId,
                                                  @NotNull Integer nRow,
                                                  @NotNull Integer pageNumber);

    List<BookingEntity> getAllBookingOfParkingLot(@NotNull Long parkingLotId,
                                                  @NotNull BookingStatusEntity bookingStatusEntity,
                                                  @NotNull Integer nRow,
                                                  @NotNull Integer pageNumber);

    List<BookingEntity> getAllOnGoingBookingOfParkingLot(@NotNull Long parkingLotId);

    Optional<BookingEntity> getFirstByCustomerIdAndIsFinished(@NotNull Long customerId, @NotNull Boolean isFinished);
}

// Node: repos/cloned_ms_repos/saigonparking/service/booking-service/src/main/java/com/bht/saigonparking/service/booking/repository/custom/BookingRepositoryCustom.java:BookingRepositoryCustom.<init>
// Node: countAllBookingGroupByStatus
// Node: countAllBookingOfParkingLotGroupByStatus
// Node: countAllBooking
// Node: countAllBookingOfCustomer
// Node: countAllBookingOfParkingLot
// Node: countAllOnGoingBookingOfParkingLot
// Node: getAllBooking
// Node: getAllBookingOfCustomer
// Node: getAllBookingOfParkingLot
// Node: getAllOnGoingBookingOfParkingLot
// Node: getFirstByCustomerIdAndIsFinished
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

// Node: shortValue
package com.bht.saigonparking.service.booking.repository.custom.impl;

import java.util.List;
import java.util.Optional;

import javax.persistence.Tuple;
import javax.validation.constraints.NotNull;

import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

import com.bht.saigonparking.common.base.BaseRepositoryCustom;
import com.bht.saigonparking.service.booking.entity.BookingEntity;
import com.bht.saigonparking.service.booking.entity.BookingStatusEntity;
import com.bht.saigonparking.service.booking.repository.custom.BookingRepositoryCustom;

/**
 *
 * @author bht
 */
@Repository
@Transactional
public class BookingRepositoryCustomImpl extends BaseRepositoryCustom implements BookingRepositoryCustom {

    @Override
    public List<Tuple> countAllBookingGroupByStatus() {
        String getCountGroupByQuery = "SELECT B.bookingStatusEntity.id, COUNT(B.id) " +
                "FROM BookingEntity B " +
                "GROUP BY B.bookingStatusEntity.id ";

        return entityManager.createQuery(getCountGroupByQuery, Tuple.class)
                .getResultList();
    }

    @Override
    public List<Tuple> countAllBookingOfParkingLotGroupByStatus(@NotNull Long parkingLotId) {
        String getCountGroupByQuery = "SELECT B.bookingStatusEntity.id, COUNT(B.id) " +
                "FROM BookingEntity B " +
                "WHERE B.parkingLotId = :parkingLotId " +
                "GROUP BY B.bookingStatusEntity.id ";

        return entityManager.createQuery(getCountGroupByQuery, Tuple.class)
                .setParameter("parkingLotId", parkingLotId)
                .getResultList();
    }

    @Override
    public Long countAllBooking() {

        String countAllQuery = "SELECT COUNT (B.id) " +
                "FROM BookingEntity B ";

        return entityManager.createQuery(countAllQuery, Long.class)
                .getSingleResult();
    }

    @Override
    public Long countAllBooking(@NotNull BookingStatusEntity bookingStatusEntity) {

        String countAllQuery = "SELECT COUNT (B.id) " +
                "FROM BookingEntity B " +
                "WHERE B.bookingStatusEntity = :bookingStatusEntity ";

        return entityManager.createQuery(countAllQuery, Long.class)
                .setParameter("bookingStatusEntity", bookingStatusEntity)
                .getSingleResult();
    }

    @Override
    public Long countAllBookingOfCustomer(@NotNull Long customerId) {

        String countAllQuery = "SELECT COUNT (B.id) " +
                "FROM BookingEntity B " +
                "WHERE B.customerId = :customerId ";

        return entityManager.createQuery(countAllQuery, Long.class)
                .setParameter("customerId", customerId)
                .getSingleResult();
    }

    @Override
    public Long countAllBookingOfParkingLot(@NotNull Long parkingLotId) {

        String countAllQuery = "SELECT COUNT (B.id) " +
                "FROM BookingEntity B " +
                "WHERE B.parkingLotId = :parkingLotId ";

        return entityManager.createQuery(countAllQuery, Long.class)
                .setParameter("parkingLotId", parkingLotId)
                .getSingleResult();
    }

    @Override
    public Long countAllBookingOfParkingLot(@NotNull Long parkingLotId,
                                            @NotNull BookingStatusEntity bookingStatusEntity) {

        String countAllQuery = "SELECT COUNT (B.id) " +
                "FROM BookingEntity B " +
                "WHERE B.parkingLotId = :parkingLotId " +
                "AND B.bookingStatusEntity = :bookingStatusEntity ";

        return entityManager.createQuery(countAllQuery, Long.class)
                .setParameter("parkingLotId", parkingLotId)
                .setParameter("bookingStatusEntity", bookingStatusEntity)
                .getSingleResult();
    }

    @Override
    public Long countAllOnGoingBookingOfParkingLot(@NotNull Long parkingLotId) {

        String countAllQuery = "SELECT COUNT (B.id) " +
                "FROM BookingEntity B " +
                "WHERE B.parkingLotId = :parkingLotId " +
                "AND B.isFinished = FALSE ";

        return entityManager.createQuery(countAllQuery, Long.class)
                .setParameter("parkingLotId", parkingLotId)
                .getSingleResult();
    }

    @Override
    public List<BookingEntity> getAllBooking(@NotNull Integer nRow,
                                             @NotNull Integer pageNumber) {

        String getAllQuery = "SELECT B " +
                "FROM BookingEntity B " +
                "JOIN FETCH B.bookingStatusEntity " +
                "LEFT JOIN FETCH B.bookingRatingEntity " +
                "ORDER BY B.id DESC ";

        return entityManager.createQuery(getAllQuery, BookingEntity.class)
                .setFirstResult(nRow * (pageNumber - 1))
                .setMaxResults(nRow)
                .getResultList();
    }

    @Override
    public List<BookingEntity> getAllBooking(@NotNull BookingStatusEntity bookingStatusEntity,
                                             @NotNull Integer nRow,
                                             @NotNull Integer pageNumber) {

        String getAllQuery = "SELECT B " +
                "FROM BookingEntity B " +
                "JOIN FETCH B.bookingStatusEntity " +
                "LEFT JOIN FETCH B.bookingRatingEntity " +
                "WHERE B.bookingStatusEntity = :bookingStatusEntity " +
                "ORDER BY B.id DESC ";

        return entityManager.createQuery(getAllQuery, BookingEntity.class)
                .setParameter("bookingStatusEntity", bookingStatusEntity)
                .setFirstResult(nRow * (pageNumber - 1))
                .setMaxResults(nRow)
                .getResultList();
    }

    @Override
    public List<BookingEntity> getAllBookingOfCustomer(@NotNull Long customerId,
                                                       @NotNull Integer nRow,
                                                       @NotNull Integer pageNumber) {

        String getAllQuery = "SELECT B " +
                "FROM BookingEntity B " +
                "JOIN FETCH B.bookingStatusEntity " +
                "LEFT JOIN FETCH B.bookingRatingEntity " +
                "WHERE B.customerId = :customerId " +
                "ORDER BY B.id DESC ";

        return entityManager.createQuery(getAllQuery, BookingEntity.class)
                .setParameter("customerId", customerId)
                .setFirstResult(nRow * (pageNumber - 1))
                .setMaxResults(nRow)
                .getResultList();
    }

    @Override
    public List<BookingEntity> getAllBookingOfParkingLot(@NotNull Long parkingLotId,
                                                         @NotNull Integer nRow,
                                                         @NotNull Integer pageNumber) {

        String getAllQuery = "SELECT B " +
                "FROM BookingEntity B " +
                "JOIN FETCH B.bookingStatusEntity " +
                "LEFT JOIN FETCH B.bookingRatingEntity " +
                "WHERE B.parkingLotId = :parkingLotId " +
                "ORDER BY B.id DESC ";

        return entityManager.createQuery(getAllQuery, BookingEntity.class)
                .setParameter("parkingLotId", parkingLotId)
                .setFirstResult(nRow * (pageNumber - 1))
                .setMaxResults(nRow)
                .getResultList();
    }

    @Override
    public List<BookingEntity> getAllBookingOfParkingLot(@NotNull Long parkingLotId,
                                                         @NotNull BookingStatusEntity bookingStatusEntity,
                                                         @NotNull Integer nRow,
                                                         @NotNull Integer pageNumber) {

        String getAllQuery = "SELECT B " +
                "FROM BookingEntity B " +
                "JOIN FETCH B.bookingStatusEntity " +
                "LEFT JOIN FETCH B.bookingRatingEntity " +
                "WHERE B.parkingLotId = :parkingLotId " +
                "AND B.bookingStatusEntity = :bookingStatusEntity " +
                "ORDER BY B.id DESC ";

        return entityManager.createQuery(getAllQuery, BookingEntity.class)
                .setParameter("parkingLotId", parkingLotId)
                .setParameter("bookingStatusEntity", bookingStatusEntity)
                .setFirstResult(nRow * (pageNumber - 1))
                .setMaxResults(nRow)
                .getResultList();
    }

    @Override
    public List<BookingEntity> getAllOnGoingBookingOfParkingLot(@NotNull Long parkingLotId) {

        String getAllQuery = "SELECT B " +
                "FROM BookingEntity B " +
                "JOIN FETCH B.bookingStatusEntity " +
                "LEFT JOIN FETCH B.bookingRatingEntity " +
                "WHERE B.parkingLotId = :parkingLotId " +
                "AND B.isFinished = FALSE " +
                "ORDER BY B.id DESC ";

        return entityManager.createQuery(getAllQuery, BookingEntity.class)
                .setParameter("parkingLotId", parkingLotId)
                .getResultList();
    }

    @Override
    public Optional<BookingEntity> getFirstByCustomerIdAndIsFinished(@NotNull Long customerId,
                                                                     @NotNull Boolean isFinished) {

        String query = "SELECT B " +
                "FROM BookingEntity B " +
                "JOIN FETCH B.bookingStatusEntity " +
                "LEFT JOIN FETCH B.bookingRatingEntity " +
                "WHERE B.customerId = :customerId " +
                "AND B.isFinished = :isFinished ";

        return Optional.ofNullable(entityManager
                .createQuery(query, BookingEntity.class)
                .setParameter("customerId", customerId)
                .setParameter("isFinished", isFinished)
                .setMaxResults(1)
                .getSingleResult());
    }
}

// Node: ofNullable
package com.bht.saigonparking.service.booking.repository.core;

import java.util.Optional;
import java.util.UUID;

import javax.validation.constraints.NotNull;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import com.bht.saigonparking.service.booking.entity.BookingEntity;
import com.bht.saigonparking.service.booking.repository.custom.BookingRepositoryCustom;

/**
 *
 * @author bht
 */
@Repository
public interface BookingRepository extends JpaRepository<BookingEntity, Long>, BookingRepositoryCustom {

    @Query("SELECT B " +
            "FROM BookingEntity B " +
            "JOIN FETCH B.bookingStatusEntity " +
            "LEFT JOIN FETCH B.bookingRatingEntity " +
            "WHERE B.uuid = ?1")
    Optional<BookingEntity> getBookingByUuid(@NotNull UUID uuid);

    @Query("SELECT B " +
            "FROM BookingEntity B " +
            "JOIN FETCH B.bookingHistoryEntitySet H " +
            "JOIN FETCH H.bookingStatusEntity " +
            "LEFT JOIN FETCH B.bookingRatingEntity " +
            "WHERE B.uuid = ?1")
    Optional<BookingEntity> getBookingDetailByUuid(@NotNull UUID uuid);

    /**
     *
     * self-implement countUnfinishedBookingByUserId method
     * using to check if user has on going booking
     */
    @Query("SELECT COUNT (B.id) " +
            "FROM BookingEntity B " +
            "WHERE B.customerId = ?1 AND B.isFinished = FALSE")
    Long countAllUnfinishedBookingByCustomerId(@NotNull Long userId);
}

// Node: repos/cloned_ms_repos/saigonparking/service/booking-service/src/main/java/com/bht/saigonparking/service/booking/repository/core/BookingRepository.java:BookingRepository.<init>
// Node: getBookingByUuid
// Node: getBookingDetailByUuid
// Node: countAllUnfinishedBookingByCustomerId
// Node: checkCustomerHasOnGoingBooking
// Node: getCustomerId
// Node: saveNewBookingHistory
// Node: deleteBookingByUuid
// Node: finishBooking
// Node: getOnGoingBookingOfCustomer
// Node: createBookingRating
// Node: updateBookingRating
// Node: deleteBookingRating
package com.bht.saigonparking.service.booking.service.main;

import java.util.List;
import java.util.Map;
import java.util.Set;

import javax.persistence.Tuple;
import javax.validation.constraints.Max;
import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;

import org.hibernate.validator.constraints.Range;
import org.springframework.data.util.Pair;

import com.bht.saigonparking.service.booking.entity.BookingEntity;
import com.bht.saigonparking.service.booking.entity.BookingHistoryEntity;
import com.bht.saigonparking.service.booking.entity.BookingRatingEntity;
import com.bht.saigonparking.service.booking.entity.BookingStatisticEntity;
import com.bht.saigonparking.service.booking.entity.BookingStatusEntity;

/**
 *
 * @author bht
 */
public interface BookingService {

    /* getOnGoingBookingOfCustomer not JOIN bookingHistorySet */
    BookingEntity getOnGoingBookingOfCustomer(@NotNull Long customerId);

    /* getBookingById not JOIN bookingHistorySet */
    BookingEntity getBookingByUuid(@NotEmpty String uuidString);

    /* getBookingById JOIN FETCH bookingHistorySet */
    BookingEntity getBookingDetailByUuid(@NotEmpty String uuidString);

    Pair<String, String> saveNewBooking(@NotNull BookingEntity bookingEntity);

    /* update status of one booking */
    void saveNewBookingHistory(@NotNull BookingHistoryEntity bookingHistoryEntity,
                               @NotEmpty String uuidString);

    void deleteBookingByUuid(@NotEmpty String uuidString);

    Pair<Long, Long> finishBooking(@NotEmpty String uuidString);

    Long countAllBooking();

    Long countAllBooking(@NotNull BookingStatusEntity bookingStatusEntity);

    Long countAllBookingOfCustomer(@NotNull Long customerId);

    Long countAllBookingOfParkingLot(@NotNull Long parkingLotId);

    Long countAllBookingOfParkingLot(@NotNull Long parkingLotId,
                                     @NotNull BookingStatusEntity bookingStatusEntity);

    Long countAllOnGoingBookingOfParkingLot(@NotNull Long parkingLotId);

    List<BookingEntity> getAllBooking(@NotNull Integer nRow,
                                      @NotNull Integer pageNumber);

    List<BookingEntity> getAllBooking(@NotNull BookingStatusEntity bookingStatusEntity,
                                      @NotNull Integer nRow,
                                      @NotNull Integer pageNumber);

    List<BookingEntity> getAllBookingOfCustomer(@NotNull Long customerId,
                                                @NotNull Integer nRow,
                                                @NotNull Integer pageNumber);

    List<BookingEntity> getAllBookingOfParkingLot(@NotNull Long parkingLotId,
                                                  @NotNull Integer nRow,
                                                  @NotNull Integer pageNumber);

    List<BookingEntity> getAllBookingOfParkingLot(@NotNull Long parkingLotId,
                                                  @NotNull BookingStatusEntity bookingStatusEntity,
                                                  @NotNull Integer nRow,
                                                  @NotNull Integer pageNumber);

    List<BookingEntity> getAllOnGoingBookingOfParkingLot(@NotNull Long parkingLotId);

    Map<Long, Long> countAllBookingGroupByStatus();

    Map<Long, Long> countAllBookingOfParkingLotGroupByStatus(@NotNull Long parkingLotId);

    boolean checkCustomerHasOnGoingBooking(@NotNull Long customerId);

    Long countAllRatingsOfParkingLot(@NotNull Long parkingLotId);

    Long countAllRatingsOfParkingLot(@NotNull Long parkingLotId, @NotNull @Range(max = 5L) Integer rating);

    Map<Tuple, String> getAllRatingsOfParkingLot(@NotNull Long parkingLotId,
                                                 boolean sortLastUpdatedAsc,
                                                 @NotNull @Max(20L) Integer nRow,
                                                 @NotNull Integer pageNumber);

    Map<Tuple, String> getAllRatingsOfParkingLot(@NotNull Long parkingLotId,
                                                 @NotNull @Range(max = 5L) Integer rating,
                                                 boolean sortLastUpdatedAsc,
                                                 @NotNull @Max(20L) Integer nRow,
                                                 @NotNull Integer pageNumber);

    Map<Integer, Long> getParkingLotRatingCountGroupByRating(@NotNull Long parkingLotId);

    Long createBookingRating(@NotNull Long customerId,
                             @NotEmpty String bookingUuidString,
                             @NotNull Integer rating,
                             @NotEmpty String comment);

    void updateBookingRating(@NotNull Long customerId,
                             @NotEmpty String bookingUuidString,
                             @NotNull Integer rating,
                             @NotEmpty String comment);

    void deleteBookingRating(@NotNull Long customerId, @NotEmpty String bookingUuidString);

    Pair<BookingRatingEntity, String> getBookingRatingWithCustomerUsernameByBookingUuid(@NotEmpty String bookingUuidString);

    void createOneOrManyParkingLotStatistic(@NotNull Set<Long> parkingLotIdSet);

    void deleteOneOrManyParkingLotStatistic(@NotNull Set<Long> parkingLotIdSet);

    BookingStatisticEntity getParkingLotBookingAndRatingStatistic(@NotNull Long parkingLotId);
}

// Node: repos/cloned_ms_repos/saigonparking/service/booking-service/src/main/java/com/bht/saigonparking/service/booking/service/main/BookingService.java:BookingService.<init>
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

// Node: getIsFinished
// Node: setBookingEntity
// Node: BookingAlreadyFinishedException
// Node: getBookingStatusEntity
// Node: BookingNotYetAcceptedException
// Node: bookingStatusEntity
// Node: version
// Node: addAllUserId
// Node: getUsernameMap
// Node: getBookingRatingEntity
// Node: bookingEntity
// Node: rating
// Node: comment
// Node: BookingAlreadyRatedException
// Node: BookingNotYetFinishedException
// Node: setRating
// Node: setComment
// Node: BookingNotYetRatedException
// Node: setBookingRatingEntity
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

// Node: notifyBookingFinish
