// Cluster 44

// Node: decryptUserId
// Node: replace
// Node: builder
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

// Node: parserBuilder
// Node: setSigningKey
// Node: parseClaimsJws
// Node: getBody
// Node: tokenId
// Node: tokenType
// Node: userId
// Node: getSubject
// Node: userRole
// Node: exp
// Node: getExpiration
// Node: fromString
package com.bht.saigonparking.service.auth.repository;

import java.util.Optional;
import java.util.UUID;

import javax.validation.constraints.NotEmpty;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import com.bht.saigonparking.service.auth.entity.UserTokenEntity;

/**
 *
 * @author bht
 */
@Repository
public interface UserTokenRepository extends JpaRepository<UserTokenEntity, Long> {

    /**
     * self-implement findByTokenId method
     * in order to prevent N+1 problem
     * using optional to catch null return
     */
    @Query("SELECT UT " +
            "FROM UserTokenEntity UT " +
            "WHERE UT.tokenId = ?1")
    Optional<UserTokenEntity> findByTokenId(@NotEmpty UUID tokenId);
}

// Node: repos/cloned_ms_repos/saigonparking/service/auth-service/src/main/java/com/bht/saigonparking/service/auth/repository/UserTokenRepository.java:UserTokenRepository.<init>
// Node: Query
// Node: findByTokenId
// Node: checkUsernameAlreadyExist
// Node: checkEmailAlreadyExist
// Node: updateUserLastSignIn
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

// Node: activateUserWithId
// Node: activateUser
// Node: saveUserRefreshToken
// Node: findById
// Node: orElseThrow
// Node: setTokenId
// Node: saveAndFlush
// Node: createCustomer
// Node: getUserById
// Node: getById
package com.bht.saigonparking.service.parkinglot.repository.core;

import java.util.List;
import java.util.Optional;

import javax.validation.constraints.NotNull;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import com.bht.saigonparking.service.parkinglot.entity.ParkingLotEmployeeEntity;
import com.bht.saigonparking.service.parkinglot.repository.custom.ParkingLotEmployeeRepositoryCustom;

/**
 *
 * @author bht
 */
@Repository
public interface ParkingLotEmployeeRepository extends JpaRepository<ParkingLotEmployeeEntity, Long>, ParkingLotEmployeeRepositoryCustom {

    /**
     *
     * self-implement countByUsername method
     * in order to prevent N+1 problem
     */
    @Query("SELECT E " +
            "FROM ParkingLotEmployeeEntity E " +
            "JOIN FETCH E.parkingLotEntity P " +
            "JOIN FETCH P.parkingLotTypeEntity " +
            "JOIN FETCH P.parkingLotLimitEntity " +
            "JOIN FETCH P.parkingLotInformationEntity " +
            "WHERE E.userId = ?1")
    Optional<ParkingLotEmployeeEntity> getByEmployeeId(@NotNull Long employeeId);

    /**
     *
     * self-implement countByUsername method
     * using to check if username already exist
     */
    @Query("SELECT COUNT (E.id) " +
            "FROM ParkingLotEmployeeEntity E " +
            "WHERE E.userId = ?1")
    Long countByUserId(@NotNull Long userId);

    /**
     *
     * self-implement getEmployeeManageParkingLotIdList method
     * using to get all employees who manage this parking-lot
     */
    @Query("SELECT E.userId " +
            "FROM ParkingLotEmployeeEntity E " +
            "WHERE E.parkingLotEntity.id = ?1")
    List<Long> getEmployeeManageParkingLotIdList(@NotNull Long parkingLotId);
}

// Node: repos/cloned_ms_repos/saigonparking/service/parkinglot-service/src/main/java/com/bht/saigonparking/service/parkinglot/repository/core/ParkingLotEmployeeRepository.java:ParkingLotEmployeeRepository.<init>
// Node: getByEmployeeId
// Node: countByUserId
// Node: getEmployeeManageParkingLotIdList
package com.bht.saigonparking.service.parkinglot.repository.core;

import java.util.List;
import java.util.Optional;
import java.util.Set;

import javax.persistence.Tuple;
import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import com.bht.saigonparking.service.parkinglot.entity.ParkingLotEntity;
import com.bht.saigonparking.service.parkinglot.repository.custom.ParkingLotRepositoryCustom;

/**
 *
 * @author bht
 */
@Repository
public interface ParkingLotRepository extends JpaRepository<ParkingLotEntity, Long>, ParkingLotRepositoryCustom {

    /**
     *
     * self-implement getById method
     * in order to prevent N+1 problem
     */
    @Query("SELECT PL " +
            "FROM ParkingLotEntity PL " +
            "JOIN FETCH PL.parkingLotTypeEntity PLT " +
            "JOIN FETCH PL.parkingLotLimitEntity PLL " +
            "JOIN FETCH PL.parkingLotInformationEntity PLI " +
            "WHERE PL.id = ?1")
    Optional<ParkingLotEntity> getById(@NotNull Long id);


    /**
     *
     * self-implement getByEmployeeId method
     * in order to prevent N+1 problem
     */
    @Query("SELECT PL " +
            "FROM ParkingLotEntity PL " +
            "JOIN FETCH PL.parkingLotTypeEntity PLT " +
            "JOIN FETCH PL.parkingLotLimitEntity PLL " +
            "JOIN FETCH PL.parkingLotInformationEntity PLI " +
            "WHERE PL.id = (" +
            "SELECT PLE.parkingLotEntity.id " +
            "FROM ParkingLotEmployeeEntity PLE " +
            "WHERE PLE.userId = ?1 " +
            ")")
    Optional<ParkingLotEntity> getByEmployeeId(@NotNull Long employeeId);


    /**
     *
     * self-implement getAll method
     * in order to prevent N+1 problem
     */
    @Query("SELECT P " +
            "FROM ParkingLotEntity P " +
            "JOIN FETCH P.parkingLotTypeEntity PLT " +
            "JOIN FETCH P.parkingLotLimitEntity PLL " +
            "JOIN FETCH P.parkingLotInformationEntity PLI " +
            "WHERE P.id IN ?1")
    List<ParkingLotEntity> getAll(@NotEmpty Set<Long> parkingLotIdList);


    @Query("SELECT FUNCTION('dbo.CHECK_AVAILABILITY', P.id) " +
            "FROM ParkingLotEntity P " +
            "WHERE P.id = ?1")
    Boolean checkAvailability(@NotNull Long parkingLotId);


    @Query("SELECT P.id " +
            "FROM ParkingLotEntity P " +
            "WHERE P.id IN ?1 " +
            "AND (P.isAvailable = FALSE " +
            "OR CURRENT_TIME NOT BETWEEN P.openingHour AND P.closingHour)")
    List<Long> checkUnavailability(@NotEmpty List<Long> parkingLotIdList);


    @SuppressWarnings({"SpringDataRepositoryMethodReturnTypeInspection", "SqlResolve", "SqlDialectInspection", "SqlNoDataSourceInspection", "RedundantSuppression"})
    @Query(value = "SELECT P.ID, P.PARKING_LOT_TYPE_ID, P.LATITUDE, P.LONGITUDE, PLL.AVAILABILITY, PLL.CAPACITY " +
            "FROM PARKING_LOT P " +
            "INNER JOIN (SELECT ID, CAPACITY, AVAILABILITY FROM PARKING_LOT_LIMIT) AS PLL ON PLL.ID = P.ID " +
            "AND 1 = dbo.IS_VALUE_IN_BOUND(P.LATITUDE, ?1, dbo.CALCULATE_DELTA_LAT_IN_DEGREE(?1, ?2, ?3)) " +
            "AND 1 = dbo.IS_VALUE_IN_BOUND(P.LONGITUDE, ?2, dbo.CALCULATE_DELTA_LNG_IN_DEGREE(?1, ?2, ?3)) " +
            "AND 1 = P.IS_AVAILABLE " +
            "AND CONVERT(TIME, GETDATE()) BETWEEN P.OPENING_HOUR AND P.CLOSING_HOUR " +
            "ORDER BY dbo.GET_DISTANCE_IN_KILOMETRE(?1, ?2, P.LATITUDE, P.LONGITUDE) " +
            "OFFSET 0 ROWS FETCH NEXT ?4 ROWS ONLY", nativeQuery = true)
    List<Tuple> getTopParkingLotInRegionOrderByDistanceWithoutName(
            @NotNull Double lat,
            @NotNull Double lng,
            @NotNull Integer radius,
            @NotNull Integer nResult);


    @SuppressWarnings({"SpringDataRepositoryMethodReturnTypeInspection", "SqlResolve", "SqlDialectInspection", "SqlNoDataSourceInspection", "RedundantSuppression"})
    @Query(value = "SELECT P.ID, PLI.NAME, P.PARKING_LOT_TYPE_ID, P.LATITUDE, P.LONGITUDE, PLL.AVAILABILITY, PLL.CAPACITY " +
            "FROM PARKING_LOT P " +
            "INNER JOIN (SELECT ID, NAME FROM PARKING_LOT_INFORMATION) AS PLI ON PLI.ID = P.ID " +
            "INNER JOIN (SELECT ID, CAPACITY, AVAILABILITY FROM PARKING_LOT_LIMIT) AS PLL ON PLL.ID = P.ID " +
            "AND 1 = dbo.IS_VALUE_IN_BOUND(P.LATITUDE, ?1, dbo.CALCULATE_DELTA_LAT_IN_DEGREE(?1, ?2, ?3)) " +
            "AND 1 = dbo.IS_VALUE_IN_BOUND(P.LONGITUDE, ?2, dbo.CALCULATE_DELTA_LNG_IN_DEGREE(?1, ?2, ?3)) " +
            "AND 1 = P.IS_AVAILABLE " +
            "AND CONVERT(TIME, GETDATE()) BETWEEN P.OPENING_HOUR AND P.CLOSING_HOUR " +
            "ORDER BY dbo.GET_DISTANCE_IN_KILOMETRE(?1, ?2, P.LATITUDE, P.LONGITUDE) " +
            "OFFSET 0 ROWS FETCH NEXT ?4 ROWS ONLY", nativeQuery = true)
    List<Tuple> getTopParkingLotInRegionOrderByDistanceWithName(
            @NotNull Double latitude,
            @NotNull Double longitude,
            @NotNull Integer radius,
            @NotNull Integer nResult);
}

// Node: repos/cloned_ms_repos/saigonparking/service/parkinglot-service/src/main/java/com/bht/saigonparking/service/parkinglot/repository/core/ParkingLotRepository.java:ParkingLotRepository.<init>
// Node: FUNCTION
// Node: checkAvailability
// Node: AND
// Node: checkUnavailability
// Node: JOIN
// Node: IS_VALUE_IN_BOUND
// Node: CALCULATE_DELTA_LAT_IN_DEGREE
// Node: CALCULATE_DELTA_LNG_IN_DEGREE
// Node: CONVERT
// Node: GETDATE
// Node: GET_DISTANCE_IN_KILOMETRE
// Node: getTopParkingLotInRegionOrderByDistanceWithoutName
// Node: getTopParkingLotInRegionOrderByDistanceWithName
package com.bht.saigonparking.service.parkinglot.repository.core;

import javax.validation.constraints.NotNull;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import com.bht.saigonparking.service.parkinglot.entity.ParkingLotLimitEntity;

/**
 *
 * @author bht
 */
@Repository
public interface ParkingLotLimitRepository extends JpaRepository<ParkingLotLimitEntity, Long> {

    /**
     *
     * self-implement getById method
     * in order to prevent N+1 problem
     */
    @Query("SELECT PLL " +
            "FROM ParkingLotLimitEntity PLL " +
            "JOIN FETCH PLL.parkingLotEntity PL " +
            "JOIN FETCH PL.parkingLotTypeEntity PLT " +
            "JOIN FETCH PL.parkingLotInformationEntity PLI " +
            "WHERE PLL.id = ?1")
    ParkingLotLimitEntity getById(@NotNull Long id);


    @Modifying
    @Query("UPDATE ParkingLotLimitEntity PLL " +
            "SET PLL.availableSlot = ?1, PLL.version = PLL.version + 1 " +
            "WHERE PLL.availableSlot <> ?1 AND PLL.parkingLotEntity.id = ?2")
    void updateAvailability(@NotNull Short newAvailability, @NotNull Long parkingLotId);
}

// Node: repos/cloned_ms_repos/saigonparking/service/parkinglot-service/src/main/java/com/bht/saigonparking/service/parkinglot/repository/core/ParkingLotLimitRepository.java:ParkingLotLimitRepository.<init>
// Node: updateAvailability
// Node: getParkingLotById
// Node: getParkingLotLimitById
// Node: deleteParkingLotById
// Node: deleteMultiParkingLotById
// Node: addEmployeeOfParkingLot
// Node: removeEmployeeOfParkingLot
// Node: checkEmployeeAlreadyManageParkingLot
// Node: getParkingLotByEmployeeId
package com.bht.saigonparking.service.parkinglot.service.main;

import java.util.List;
import java.util.Map;
import java.util.Set;

import javax.persistence.Tuple;
import javax.validation.constraints.Max;
import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;

import com.bht.saigonparking.service.parkinglot.entity.ParkingLotEntity;
import com.bht.saigonparking.service.parkinglot.entity.ParkingLotInformationEntity;
import com.bht.saigonparking.service.parkinglot.entity.ParkingLotLimitEntity;
import com.bht.saigonparking.service.parkinglot.entity.ParkingLotTypeEntity;

/**
 *
 * @author bht
 */
public interface ParkingLotService {

    Long getParkingLotIdByParkingLotEmployeeId(@NotNull Long parkingLotEmployeeId);

    Long countAll(@NotEmpty String keyword, boolean isAvailableOnly);

    Long countAll(@NotEmpty String keyword, boolean isAvailableOnly,
                  @NotNull ParkingLotTypeEntity parkingLotTypeEntity);

    List<ParkingLotEntity> getAll(@NotNull Set<Long> parkingLotIdSet);

    List<ParkingLotEntity> getAll(@NotNull @Max(20L) Integer nRow,
                                  @NotNull Integer pageNumber,
                                  @NotEmpty String keyword,
                                  boolean isAvailableOnly);

    List<ParkingLotEntity> getAll(@NotNull @Max(20L) Integer nRow,
                                  @NotNull Integer pageNumber,
                                  @NotEmpty String keyword,
                                  boolean isAvailableOnly,
                                  @NotNull ParkingLotTypeEntity parkingLotTypeEntity);

    ParkingLotEntity getParkingLotById(@NotNull Long id);

    ParkingLotEntity getParkingLotByEmployeeId(@NotNull Long parkingLotEmployeeId);

    ParkingLotLimitEntity getParkingLotLimitById(@NotNull Long id);

    Boolean checkAvailability(@NotNull Long parkingLotId);

    List<Long> checkUnavailability(@NotEmpty List<Long> parkingLotIdList);

    List<Tuple> getTopParkingLotInRegionOrderByDistanceWithoutName(@NotNull Double lat,
                                                                   @NotNull Double lng,
                                                                   @NotNull Integer radius,
                                                                   @NotNull Integer nResult);

    List<Tuple> getTopParkingLotInRegionOrderByDistanceWithName(@NotNull Double lat,
                                                                @NotNull Double lng,
                                                                @NotNull Integer radius,
                                                                @NotNull Integer nResult);

    void deleteParkingLotById(@NotNull Long id);

    void deleteMultiParkingLotById(@NotNull Set<Long> parkingLotIdSet);

    void updateAvailability(@NotNull Short newAvailability, @NotNull Long parkingLotId);

    String getParkingLotNameByParkingLotId(@NotNull Long parkingLotId);

    Map<Long, String> mapToParkingLotNameMap(@NotNull Set<Long> parkingLotIdSet);

    Map<Long, Long> countAllParkingLotGroupByType();

    Long createNewParkingLot(@NotNull ParkingLotEntity parkingLotEntity,
                             @NotNull ParkingLotLimitEntity parkingLotLimitEntity,
                             @NotNull ParkingLotInformationEntity parkingLotInformationEntity);

    boolean checkEmployeeAlreadyManageParkingLot(@NotNull Long employeeId);

    List<Long> getEmployeeManageParkingLotIdList(@NotNull Long parkingLotId);

    void addEmployeeOfParkingLot(@NotNull Long employeeId, @NotNull Long parkingLotId);

    void removeEmployeeOfParkingLot(@NotNull Long employeeId, @NotNull Long parkingLotId, boolean deleteEmployee);
}

// Node: repos/cloned_ms_repos/saigonparking/service/parkinglot-service/src/main/java/com/bht/saigonparking/service/parkinglot/service/main/ParkingLotService.java:ParkingLotService.<init>
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

// Node: delete
// Node: parkingLotEntity
// Node: deleteUserById
// Node: getByUsername
// Node: setIsActivated
package com.bht.saigonparking.service.user.repository.core;

import java.util.List;
import java.util.Optional;
import java.util.Set;

import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import com.bht.saigonparking.service.user.entity.UserEntity;
import com.bht.saigonparking.service.user.repository.custom.UserRepositoryCustom;

/**
 *
 * @author bht
 */
@Repository
public interface UserRepository extends JpaRepository<UserEntity, Long>, UserRepositoryCustom {

    /**
     *
     * self-implement countByUsername method
     * using to check if username already exist
     */
    @Query("SELECT COUNT (U.id) " +
            "FROM UserEntity U " +
            "WHERE U.username = ?1")
    Long countByUsername(@NotEmpty String username);


    /**
     *
     * self-implement countByEmail method
     * using to check if email already exist
     */
    @Query("SELECT COUNT (U.id) " +
            "FROM UserEntity U " +
            "WHERE U.email = ?1")
    Long countByEmail(@NotEmpty String email);


    /**
     *
     * self-implement getByUsername method
     * in order to prevent N+1 problem
     */
    @Query("SELECT U " +
            "FROM UserEntity U " +
            "JOIN FETCH U.userRoleEntity UR " +
            "WHERE U.username = ?1")
    Optional<UserEntity> getByUsername(@NotEmpty String username);


    /**
     *
     * self-implement getAll method
     * in order to prevent N+1 problem
     */
    @Query("SELECT U " +
            "FROM UserEntity U " +
            "JOIN FETCH U.userRoleEntity UR " +
            "WHERE U.id IN ?1")
    List<UserEntity> getAll(@NotEmpty Set<Long> userIdSet);


    /**
     *
     * self-implement getUsernameByUserId method
     * in order to prevent get all fields of User
     * use-case: booking-rating with customer username
     */
    @Query("SELECT U.username " +
            "FROM UserEntity U " +
            "WHERE U.id = ?1")
    Optional<String> getUsernameOfUser(@NotNull Long id);
}

// Node: repos/cloned_ms_repos/saigonparking/service/user-service/src/main/java/com/bht/saigonparking/service/user/repository/core/UserRepository.java:UserRepository.<init>
// Node: countByUsername
// Node: countByEmail
// Node: getUsernameOfUser
package com.bht.saigonparking.service.user.repository.core;

import java.util.Optional;

import javax.validation.constraints.NotEmpty;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import com.bht.saigonparking.service.user.entity.CustomerEntity;

/**
 *
 * @author bht
 */
@Repository
public interface CustomerRepository extends JpaRepository<CustomerEntity, Long> {

    /**
     *
     * self-implement getByUsername method
     * in order to prevent N+1 problem
     */
    @Query("SELECT C " +
            "FROM CustomerEntity C " +
            "JOIN FETCH C.userRoleEntity UR " +
            "WHERE C.username = ?1")
    Optional<CustomerEntity> getByUsername(@NotEmpty String username);
}

// Node: repos/cloned_ms_repos/saigonparking/service/user-service/src/main/java/com/bht/saigonparking/service/user/repository/core/CustomerRepository.java:CustomerRepository.<init>
// Node: getCustomerById
// Node: getCustomerByUsername
// Node: mapUserIdToUsername
// Node: createUser
// Node: updateCustomer
// Node: deactivateUserWithId
package com.bht.saigonparking.service.user.service.main;

import java.util.List;
import java.util.Map;
import java.util.Set;

import javax.validation.constraints.Max;
import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;

import com.bht.saigonparking.service.user.entity.CustomerEntity;
import com.bht.saigonparking.service.user.entity.UserEntity;
import com.bht.saigonparking.service.user.entity.UserRoleEntity;

/**
 *
 * @author bht
 */
public interface UserService {

    Long countAll(@NotEmpty String keyword, boolean inactivatedOnly);

    Long countAll(@NotEmpty String keyword, boolean inactivatedOnly, @NotNull UserRoleEntity userRoleEntity);

    List<UserEntity> getAll(@NotNull Set<Long> userIdSet);

    List<UserEntity> getAll(@NotNull @Max(20L) Integer nRow,
                            @NotNull Integer pageNumber,
                            @NotEmpty String keyword,
                            boolean inactivatedOnly);

    List<UserEntity> getAll(@NotNull @Max(20L) Integer nRow,
                            @NotNull Integer pageNumber,
                            @NotEmpty String keyword,
                            boolean inactivatedOnly,
                            @NotNull UserRoleEntity userRoleEntity);

    UserEntity getUserById(@NotNull Long id);

    UserEntity getUserByUsername(@NotEmpty String username);

    CustomerEntity getCustomerById(@NotNull Long id);

    CustomerEntity getCustomerByUsername(@NotEmpty String username);

    Long createUser(@NotNull UserEntity userEntity);

    Long createCustomer(@NotNull CustomerEntity customerEntity);

    void updateCustomer(@NotNull CustomerEntity customerEntity);

    void updateUserLastSignIn(@NotNull Long id, @NotNull Long timeInMillis);

    void activateUserWithId(@NotNull Long id);

    void deactivateUserWithId(@NotNull Long id);

    void updateUserPassword(@NotNull UserEntity userEntity, @NotEmpty String newPassword);

    void deleteUserById(@NotNull Long userId);

    void deleteMultiUserById(@NotNull Set<Long> userIdSet);

    Map<Long, String> mapToUsernameMap(@NotNull Set<Long> userIdList);

    Map<Long, Long> countAllUserGroupByRole();

    boolean checkUsernameAlreadyExist(@NotEmpty String username);

    boolean checkEmailAlreadyExist(@NotEmpty String email);

    String getUsernameOfUser(@NotNull Long userId);
}

// Node: repos/cloned_ms_repos/saigonparking/service/user-service/src/main/java/com/bht/saigonparking/service/user/service/main/UserService.java:UserService.<init>
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

// Node: setLastSignIn
// Node: Timestamp
// Node: orElse
package com.bht.saigonparking.service.booking.repository.core;

import java.util.Optional;
import java.util.UUID;

import javax.validation.constraints.NotNull;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import com.bht.saigonparking.service.booking.entity.BookingRatingEntity;
import com.bht.saigonparking.service.booking.repository.custom.BookingRatingRepositoryCustom;

/**
 *
 * @author bht
 */
public interface BookingRatingRepository extends JpaRepository<BookingRatingEntity, Long>, BookingRatingRepositoryCustom {

    @Query("SELECT R " +
            "FROM BookingRatingEntity R " +
            "JOIN FETCH R.bookingEntity B " +
            "JOIN FETCH B.bookingStatusEntity " +
            "WHERE B.uuid = ?1")
    Optional<BookingRatingEntity> getByBookingUuid(@NotNull UUID uuid);
}

// Node: repos/cloned_ms_repos/saigonparking/service/booking-service/src/main/java/com/bht/saigonparking/service/booking/repository/core/BookingRatingRepository.java:BookingRatingRepository.<init>
// Node: getByBookingUuid
package com.bht.saigonparking.service.booking.repository.core;

import java.util.Optional;

import javax.validation.constraints.NotNull;

import org.springframework.data.jpa.repository.JpaRepository;

import com.bht.saigonparking.service.booking.entity.BookingStatisticEntity;

/**
 *
 * @author bht
 */
public interface BookingStatisticRepository extends JpaRepository<BookingStatisticEntity, Long> {

    Optional<BookingStatisticEntity> getByParkingLotId(@NotNull Long parkingLotId);
}

// Node: repos/cloned_ms_repos/saigonparking/service/booking-service/src/main/java/com/bht/saigonparking/service/booking/repository/core/BookingStatisticRepository.java:BookingStatisticRepository.<init>
// Node: getByParkingLotId
// Node: getBookingRatingWithCustomerUsernameByBookingUuid
// Node: getParkingLotBookingAndRatingStatistic
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

// Node: getBookingRatingByBookingUuid
// Node: getBookingEntity
// Node: createParkingLotStatistic
// Node: isPresent
// Node: parkingLotId
// Node: nBooking
// Node: nRating
// Node: ratingAverage
// Node: deleteParkingLotStatistic
// Node: ifPresent
