// Cluster 32

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

// Node: getUserIdFromUserQueueName
// Node: matcher
// Node: find
// Node: group
// Node: valueOf
// Node: IncorrectQueueNameException
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

// Node: repos/cloned_ms_repos/saigonparking/common/src/main/java/com/bht/saigonparking/common/auth/SaigonParkingAuthenticationImpl.java:SaigonParkingAuthenticationImpl.<init>
// Node: timeBasedGenerator
// Node: Properties
// Node: load
// Node: requireNonNull
// Node: getClassLoader
// Node: getResourceAsStream
// Node: getSecretKey
// Node: encryptUserId
// Node: hmacShaKeyFor
// Node: getSecretKeyByteArray
// Node: getDecoder
// Node: decode
// Node: String
// Node: getBytes
// Node: Random
// Node: nextInt
// Node: generate
// Node: setId
// Node: setIssuer
// Node: claim
// Node: setIssuedAt
// Node: setExpiration
// Node: plus
// Node: signWith
// Node: compact
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

// Node: toTime
// Node: toTimestamp
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

// Node: generateUUID
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

// Node: consumeMessageFromQueue
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

// Node: onMessage
// Node: getMessageProperties
// Node: getConsumerQueue
// Node: fromMessage
