// Cluster 30

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

// Node: generateUserRoutingKey
// Node: getUserQueueName
// Node: getUserRoutingKey
// Node: getParkingLotExchangeName
package com.bht.saigonparking.service.parkinglot.repository.custom;

import javax.validation.constraints.NotNull;

/**
 *
 * @author bht
 */
public interface ParkingLotEmployeeRepositoryCustom {

    Long getParkingLotIdByParkingLotEmployeeId(@NotNull Long parkingLotEmployeeId);
}

// Node: repos/cloned_ms_repos/saigonparking/service/parkinglot-service/src/main/java/com/bht/saigonparking/service/parkinglot/repository/custom/ParkingLotEmployeeRepositoryCustom.java:ParkingLotEmployeeRepositoryCustom.<init>
// Node: getParkingLotIdByParkingLotEmployeeId
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

package com.bht.saigonparking.service.contact.service;

import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;

import org.springframework.amqp.core.Queue;

/**
 *
 * @author bht
 */
public interface QueueService {

    Queue registerAutoDeleteQueueForUser(@NotNull Long userId);

    void registerAutoDeleteExchangeForParkingLot(@NotNull Long parkingLotId, @NotNull Queue employeeQueue);

    boolean isExchangeExist(@NotEmpty String exchangeName);

    boolean isQueueExist(@NotEmpty String queueName);
}

// Node: repos/cloned_ms_repos/saigonparking/service/contact-service/src/main/java/com/bht/saigonparking/service/contact/service/QueueService.java:QueueService.<init>
// Node: registerAutoDeleteQueueForUser
// Node: registerAutoDeleteExchangeForParkingLot
// Node: isExchangeExist
// Node: isQueueExist
package com.bht.saigonparking.service.contact.service;

import javax.validation.constraints.NotNull;

/**
 *
 * @author bht
 */
public interface ConnectivityService {

    boolean isUserOnline(@NotNull Long userId);

    boolean isParkingLotOnline(@NotNull Long parkingLotId);
}

// Node: repos/cloned_ms_repos/saigonparking/service/contact-service/src/main/java/com/bht/saigonparking/service/contact/service/ConnectivityService.java:ConnectivityService.<init>
// Node: isUserOnline
// Node: isParkingLotOnline
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

// Node: Queue
// Node: declareQueue
// Node: declareBinding
// Node: bind
// Node: to
// Node: with
// Node: addQueues
// Node: FanoutExchange
// Node: declareExchange
// Node: execute
// Node: exchangeDeclarePassive
// Node: queueDeclarePassive
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

package com.bht.saigonparking.service.contact.service.impl;

import static com.bht.saigonparking.service.contact.configuration.WebSocketConfiguration.*;

import java.util.HashMap;
import java.util.Map;

import javax.validation.constraints.NotNull;

import org.apache.logging.log4j.Level;
import org.springframework.amqp.core.Queue;
import org.springframework.amqp.rabbit.listener.AbstractMessageListenerContainer;
import org.springframework.stereotype.Service;

import com.bht.saigonparking.api.grpc.parkinglot.ParkingLotServiceGrpc;
import com.bht.saigonparking.common.auth.SaigonParkingTokenBody;
import com.bht.saigonparking.common.exception.PostAuthenticationException;
import com.bht.saigonparking.common.util.LoggingUtil;
import com.bht.saigonparking.service.contact.service.HandshakeService;
import com.bht.saigonparking.service.contact.service.QueueService;
import com.google.protobuf.Int64Value;

import lombok.RequiredArgsConstructor;

/**
 *
 * @author bht
 */
@Service
@RequiredArgsConstructor
public final class HandshakeServiceImpl implements HandshakeService {

    private final QueueService queueService;
    private final AbstractMessageListenerContainer messageListenerContainer;
    private final ParkingLotServiceGrpc.ParkingLotServiceBlockingStub parkingLotServiceBlockingStub;

    @Override
    public Map<String, Object> postAuthentication(@NotNull SaigonParkingTokenBody tokenBody, boolean mustConsumeFromQueue) {

        Long userId = tokenBody.getUserId();
        String userRole = tokenBody.getUserRole();
        Map<String, Object> attributes = new HashMap<>();

        attributes.put(SAIGON_PARKING_USER_ID_KEY, userId);
        attributes.put(SAIGON_PARKING_USER_ROLE_KEY, userRole);
        attributes.put(SAIGON_PARKING_USER_AUXILIARY_KEY, !mustConsumeFromQueue);

        if (mustConsumeFromQueue) {

            /* register auto-delete queue for user and start listen to it for consuming incoming message */
            Queue userQueue = queueService.registerAutoDeleteQueueForUser(userId);

            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("registerAutoDeleteQueueForUser(%d)", userId));

            if ("PARKING_LOT_EMPLOYEE".equals(userRole)) {
                try {
                    long parkingLotId = parkingLotServiceBlockingStub
                            .getParkingLotIdByParkingLotEmployeeId(Int64Value.of(userId))
                            .getValue();

                    attributes.put(SAIGON_PARKING_PARKING_LOT_ID_KEY, parkingLotId);

                    /* register auto-delete exchange for parking-lot and bind user auto-delete queue to it */
                    queueService.registerAutoDeleteExchangeForParkingLot(parkingLotId, userQueue);

                    LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                            String.format("registerAutoDeleteExchangeForParkingLot(%d)", parkingLotId));

                } catch (Exception exception) {
                    /* if exception occurs, immediately remove listen to queue */
                    /* as queue has no one listen to it, it will be removed (auto-delete queue) */
                    /* as exchange has no queue bind to it, it will be removed (auto-delete exchange) */
                    messageListenerContainer.removeQueues(userQueue);
                    throw new PostAuthenticationException();
                }
            }
        } else {
            LoggingUtil.log(Level.INFO, "SERVICE", "Success",
                    String.format("connectedToAuxiliaryDeviceOfUser(%d)", userId)); /* auxiliary device: such as QR Scanner */
        }
        return attributes;
    }
}

// Node: removed
// Node: removeQueues
// Node: PostAuthenticationException
// Node: connectedToAuxiliaryDeviceOfUser
