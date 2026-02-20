// Cluster 2

// Node: containsKey
package com.bht.saigonparking.common.base;

import java.util.concurrent.Executor;

import org.springframework.aop.interceptor.AsyncUncaughtExceptionHandler;
import org.springframework.context.annotation.Bean;
import org.springframework.http.converter.protobuf.ProtobufHttpMessageConverter;
import org.springframework.scheduling.annotation.AsyncConfigurer;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

import com.bht.saigonparking.common.custom.CustomAsyncExceptionHandler;
import com.bht.saigonparking.common.spring.SpringApplicationContext;

/**
 *
 * @author bht
 */
public abstract class BaseSaigonParkingAppConfiguration implements AsyncConfigurer {

    @Bean
    public ProtobufHttpMessageConverter protobufHttpMessageConverter() {
        return new ProtobufHttpMessageConverter();
    }

    @Bean
    public SpringApplicationContext springApplicationContext() {
        return new SpringApplicationContext();
    }

    @Override
    public final Executor getAsyncExecutor() {
        return SpringApplicationContext.getBean(ThreadPoolTaskExecutor.class);
    }

    @Override
    public final AsyncUncaughtExceptionHandler getAsyncUncaughtExceptionHandler() {
        return new CustomAsyncExceptionHandler();
    }
}

// Node: getAsyncExecutor
// Node: getBean
package com.bht.saigonparking.common.util;

import com.google.protobuf.ByteString;
import com.google.protobuf.Internal;

/**
 * using this util class to encode & decode
 * to communicate between server and client
 * using protocol buffer of gRPC
 *
 * @author bht
 */
public final class ImageUtil {

    private ImageUtil() {
    }

    /**
     *
     * using from send's side
     * to encode image data
     * for sending image purpose
     */
    public static ByteString encodeImage(byte[] imageData) {
        return ByteString.copyFrom((imageData != null) ? imageData : Internal.EMPTY_BYTE_ARRAY);
    }

    /**
     *
     * using from receive's side
     * to decode image data
     * for reading image purpose
     */
    public static byte[] decodeImage(ByteString imageData) {
        return imageData.toByteArray();
    }

    /**
     *
     * using from receive's side
     * to check if the imageData received is empty or not
     */
    public static boolean isDecodedImageEmpty(byte[] imageData) {
        return imageData.length == 0;
    }
}

// Node: decodeImage
// Node: toByteArray
package com.bht.saigonparking.common.spring;

import org.springframework.context.ApplicationContext;
import org.springframework.context.ApplicationContextAware;
import org.springframework.lang.NonNull;

/**
 *
 * @author bht
 */
public final class SpringApplicationContext implements ApplicationContextAware {

    private static ApplicationContext context;

    /**
     * get bean created before by app static context
     * @param <T> any object has been injected before
     * @return Bean of a specific class
     */
    public static <T> T getBean(Class<T> beanClass) {
        return context.getBean(beanClass);
    }

    /**
     * used by Spring !!!!
     * please don't use it
     */
    @Override
    public synchronized void setApplicationContext(@NonNull ApplicationContext applicationContext) {
        context = applicationContext;
    }
}

// Node: setSubject
package com.bht.saigonparking.service.auth;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.builder.SpringApplicationBuilder;
import org.springframework.boot.web.servlet.support.SpringBootServletInitializer;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 *
 * This class is auth-service main class
 * which contains the main() method to execute the service.
 * Auth service is simply a spring-boot server
 * which communicate indirectly with the RDBMS through User Service
 *
 * @author bht
 */
@EnableScheduling
@SpringBootApplication
public class AuthService extends SpringBootServletInitializer {

    @Override
    protected SpringApplicationBuilder configure(SpringApplicationBuilder builder) {
        return builder.sources(AuthService.class);
    }

    public static void main(String[] args) {
        SpringApplication.run(AuthService.class, args);
    }
}

// Node: repos/cloned_ms_repos/saigonparking/service/auth-service/src/main/java/com/bht/saigonparking/service/auth/AuthService.java:is.<init>
// Node: main
// Node: run
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

// Node: setUserId
// Node: setTimeInMillis
// Node: currentTimeMillis
// Node: getMessage
// Node: setType
// Node: setTemporaryToken
package com.bht.saigonparking.service.parkinglot;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.builder.SpringApplicationBuilder;
import org.springframework.boot.web.servlet.support.SpringBootServletInitializer;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 *
 * This class is parking-map-service main class
 * which contains the main() method to execute the service.
 * Parking-map service is simply a spring-boot server
 * which communicate directly with the RDBMS
 *
 * @author bht
 */
@EnableScheduling
@SpringBootApplication
public class ParkingLotService extends SpringBootServletInitializer {

    @Override
    protected SpringApplicationBuilder configure(SpringApplicationBuilder builder) {
        return builder.sources(ParkingLotService.class);
    }

    public static void main(String[] args) {
        SpringApplication.run(ParkingLotService.class, args);
    }
}

// Node: repos/cloned_ms_repos/saigonparking/service/parkinglot-service/src/main/java/com/bht/saigonparking/service/parkinglot/ParkingLotService.java:is.<init>
// Node: getType
// Node: updateParkingLotAvailability
// Node: getNewAvailability
package com.bht.saigonparking.service.user;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.builder.SpringApplicationBuilder;
import org.springframework.boot.web.servlet.support.SpringBootServletInitializer;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 *
 * This class is user-service main class
 * which contains the main() method to execute the service.
 * User service is simply a spring-boot server
 * which communicate directly with the RDBMS
 *
 * @author bht
 */
@EnableScheduling
@SpringBootApplication
public class UserService extends SpringBootServletInitializer {

    @Override
    protected SpringApplicationBuilder configure(SpringApplicationBuilder builder) {
        return builder.sources(UserService.class);
    }

    public static void main(String[] args) {
        SpringApplication.run(UserService.class, args);
    }
}

// Node: repos/cloned_ms_repos/saigonparking/service/user-service/src/main/java/com/bht/saigonparking/service/user/UserService.java:is.<init>
package com.bht.saigonparking.service.booking;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.builder.SpringApplicationBuilder;
import org.springframework.boot.web.servlet.support.SpringBootServletInitializer;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 *
 * This class is booking-service main class
 * which contains the main() method to execute the service.
 * Contact service is simply a spring-boot server
 * which use for communication purposes only
 *
 * @author bht
 */
@EnableScheduling
@SpringBootApplication
public class BookingService extends SpringBootServletInitializer {

    @Override
    protected SpringApplicationBuilder configure(SpringApplicationBuilder builder) {
        return builder.sources(BookingService.class);
    }

    public static void main(String[] args) {
        SpringApplication.run(BookingService.class, args);
    }
}

// Node: repos/cloned_ms_repos/saigonparking/service/booking-service/src/main/java/com/bht/saigonparking/service/booking/BookingService.java:is.<init>
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

// Node: createBooking
// Node: CustomerHasOnGoingBookingException
// Node: saveNewBooking
// Node: setBookingId
// Node: setQrCode
// Node: setCreatedAt
// Node: getLicensePlate
// Node: setCustomerId
// Node: getUuid
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

// Node: getCreatedAt
package com.bht.saigonparking.service.mail;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.builder.SpringApplicationBuilder;
import org.springframework.boot.web.servlet.support.SpringBootServletInitializer;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 *
 * This class is mail-service main class
 * which contains the main() method to execute the service.
 * Auth service is simply a spring-boot server
 * which aim to send non-reply email to client
 *
 * @author bht
 */
@EnableScheduling
@SpringBootApplication
public class MailService extends SpringBootServletInitializer {

    @Override
    protected SpringApplicationBuilder configure(SpringApplicationBuilder builder) {
        return builder.sources(MailService.class);
    }

    public static void main(String[] args) {
        SpringApplication.run(MailService.class, args);
    }
}

// Node: repos/cloned_ms_repos/saigonparking/service/mail-service/src/main/java/com/bht/saigonparking/service/mail/MailService.java:is.<init>
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

// Node: consumeMessageFromMailTopic
// Node: sendNewMail
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

// Node: createMimeMessage
// Node: MimeMessageHelper
// Node: getTemporaryToken
// Node: setTo
// Node: setText
// Node: send
// Node: getMimeMessage
// Node: EmailToUser
package com.bht.saigonparking.service.mail.service;

import com.bht.saigonparking.api.grpc.mail.MailRequest;

/**
 *
 * @author bht
 */
public interface MailService {

    /**
     * send new email to some user
     * @param request mail request, include:
     * + mailType: activate-account or reset-password ?
     * + username: username of user to whom the mail is sent
     * + email: email of user to whom the mail is sent
     * + token: using for access, will expired in just 5 min
     */
    void sendNewMail(MailRequest request);
}

// Node: repos/cloned_ms_repos/saigonparking/service/mail-service/src/main/java/com/bht/saigonparking/service/mail/service/MailService.java:MailService.<init>
package com.bht.saigonparking.service.contact;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.builder.SpringApplicationBuilder;
import org.springframework.boot.web.servlet.support.SpringBootServletInitializer;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 *
 * This class is contact-service main class
 * which contains the main() method to execute the service.
 * Contact service is simply a spring-boot server
 * which use for communication purposes only
 *
 * @author bht
 */
@EnableScheduling
@SpringBootApplication
public class ContactService extends SpringBootServletInitializer {

    @Override
    protected SpringApplicationBuilder configure(SpringApplicationBuilder builder) {
        return builder.sources(ContactService.class);
    }

    public static void main(String[] args) {
        SpringApplication.run(ContactService.class, args);
    }
}

// Node: repos/cloned_ms_repos/saigonparking/service/contact-service/src/main/java/com/bht/saigonparking/service/contact/ContactService.java:is.<init>
package com.bht.saigonparking.service.contact.service;

import java.io.IOException;

import javax.validation.constraints.NotNull;

import org.springframework.web.socket.WebSocketSession;

import com.bht.saigonparking.api.grpc.contact.SaigonParkingMessage;

/**
 *
 * @author bht
 */
public interface MessagingService {

    void prePublishMessageToQueue(@NotNull SaigonParkingMessage.Builder delegate,
                                  @NotNull WebSocketSession webSocketSession) throws IOException;

    void publishMessageToQueue(@NotNull SaigonParkingMessage saigonParkingMessage);

    void consumeMessageFromQueue(@NotNull SaigonParkingMessage saigonParkingMessage, @NotNull Long receiverUserId);

    void forwardMessageToCustomer(@NotNull SaigonParkingMessage message);

    void forwardMessageToParkingLot(@NotNull SaigonParkingMessage message);
}

// Node: repos/cloned_ms_repos/saigonparking/service/contact-service/src/main/java/com/bht/saigonparking/service/contact/service/MessagingService.java:MessagingService.<init>
// Node: prePublishMessageToQueue
// Node: publishMessageToQueue
// Node: forwardMessageToCustomer
// Node: forwardMessageToParkingLot
package com.bht.saigonparking.service.contact.service;

import java.io.IOException;

import javax.validation.constraints.NotNull;

import org.springframework.web.socket.WebSocketSession;

import com.bht.saigonparking.api.grpc.contact.SaigonParkingMessage;
import com.google.protobuf.InvalidProtocolBufferException;

/**
 *
 * @author bht
 */
public interface IntermediateService {

    void handleBookingRequest(@NotNull SaigonParkingMessage.Builder message,
                              @NotNull WebSocketSession webSocketSession) throws IOException;

    void handleBookingCancellation(@NotNull SaigonParkingMessage.Builder message,
                                   @NotNull MessagingService messagingService) throws InvalidProtocolBufferException;

    void handleBookingAcceptance(@NotNull SaigonParkingMessage.Builder message,
                                 @NotNull MessagingService messagingService) throws InvalidProtocolBufferException;

    void handleBookingReject(@NotNull SaigonParkingMessage.Builder message,
                             @NotNull MessagingService messagingService) throws InvalidProtocolBufferException;
}

// Node: repos/cloned_ms_repos/saigonparking/service/contact-service/src/main/java/com/bht/saigonparking/service/contact/service/IntermediateService.java:IntermediateService.<init>
// Node: handleBookingRequest
// Node: handleBookingCancellation
// Node: handleBookingAcceptance
// Node: handleBookingReject
package com.bht.saigonparking.service.contact.service;

import javax.validation.constraints.NotNull;

import org.springframework.web.socket.WebSocketSession;

import com.bht.saigonparking.api.grpc.contact.SaigonParkingMessage;
import com.google.protobuf.InvalidProtocolBufferException;

/**
 *
 * @author bht
 */
public interface ContactService {

    void handleMessageSendToSystem(@NotNull SaigonParkingMessage saigonParkingMessage,
                                   @NotNull WebSocketSession session) throws InvalidProtocolBufferException;
}

// Node: repos/cloned_ms_repos/saigonparking/service/contact-service/src/main/java/com/bht/saigonparking/service/contact/service/ContactService.java:ContactService.<init>
// Node: handleMessageSendToSystem
// Node: checkUserOnlineByUserId
// Node: checkParkingLotOnlineByParkingLotId
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

// Node: repos/cloned_ms_repos/saigonparking/service/contact-service/src/main/java/com/bht/saigonparking/service/contact/service/impl/IntermediateServiceImpl.java:IntermediateServiceImpl.<init>
// Node: mergeFrom
// Node: getContent
// Node: getSenderId
// Node: setLicensePlate
// Node: getCustomerLicense
// Node: getQrCode
// Node: setSenderId
// Node: setReceiverId
// Node: setClassification
// Node: setContent
// Node: toByteString
// Node: sendMessage
// Node: BinaryMessage
// Node: parseFrom
// Node: setStatus
// Node: setNote
// Node: getReason
// Node: updateBookingStatusStreamObserver
// Node: getClassification
// Node: setTimestamp
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

// Node: repos/cloned_ms_repos/saigonparking/service/contact-service/src/main/java/com/bht/saigonparking/service/contact/service/impl/ContactServiceImpl.java:ContactServiceImpl.<init>
// Node: getUserRoleFromSession
// Node: setNewAvailability
// Node: lot
// Node: getUserAuxiliaryFromSession
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

// Node: repos/cloned_ms_repos/saigonparking/service/contact-service/src/main/java/com/bht/saigonparking/service/contact/service/impl/MessagingServiceImpl.java:MessagingServiceImpl.<init>
// Node: getUserIdFromSession
// Node: getParkingLotIdFromSession
// Node: preProcessingMessage
// Node: getAllSessionOfUser
// Node: filter
// Node: forwardMessageToReceiver
// Node: size
// Node: getReceiverId
// Node: isSessionConsumeMessageFromQueue
package com.bht.saigonparking.service.contact.handler;

import static com.bht.saigonparking.api.grpc.contact.SaigonParkingMessage.Classification.SYSTEM_MESSAGE;
import static com.bht.saigonparking.api.grpc.contact.SaigonParkingMessage.Type.ERROR;
import static com.bht.saigonparking.api.grpc.contact.SaigonParkingMessage.Type.NOTIFICATION;

import java.io.IOException;

import org.apache.logging.log4j.Level;
import org.springframework.lang.NonNull;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.BinaryMessage;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.BinaryWebSocketHandler;

import com.bht.saigonparking.api.grpc.contact.ErrorContent;
import com.bht.saigonparking.api.grpc.contact.NotificationContent;
import com.bht.saigonparking.api.grpc.contact.SaigonParkingMessage;
import com.bht.saigonparking.common.util.LoggingUtil;
import com.bht.saigonparking.service.contact.service.ContactService;
import com.bht.saigonparking.service.contact.service.MessagingService;

import io.grpc.StatusRuntimeException;
import lombok.RequiredArgsConstructor;

/**
 *
 * @author bht
 */
@Component
@RequiredArgsConstructor
public class WebSocketBinaryMessageHandler extends BinaryWebSocketHandler {

    private static final String LOGGING_KEY = "WebSocketBinaryMessageHandler";
    private final WebSocketUserSessionManagement webSocketUserSessionManagement;
    private final ContactService contactService;
    private final MessagingService messagingService;

    @Override
    public void afterConnectionEstablished(@NonNull WebSocketSession session) throws IOException {
        Long userId = webSocketUserSessionManagement.getUserIdFromSession(session);
        webSocketUserSessionManagement.addNewUserSession(userId, session);
        LoggingUtil.log(Level.INFO, LOGGING_KEY, "connectionEstablishedWithUser", userId.toString());

        NotificationContent notificationContent = NotificationContent.newBuilder()
                .setNotification("Connection to Contact service established !")
                .build();

        SaigonParkingMessage saigonParkingMessage = SaigonParkingMessage.newBuilder()
                .setClassification(SYSTEM_MESSAGE)
                .setType(NOTIFICATION)
                .setSenderId(0)
                .setReceiverId(userId)
                .setContent(notificationContent.toByteString())
                .build();

        session.sendMessage(new BinaryMessage(saigonParkingMessage.toByteArray()));
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
    protected void handleBinaryMessage(@NonNull WebSocketSession session, @NonNull BinaryMessage message) throws Exception {
        Long userId = webSocketUserSessionManagement.getUserIdFromSession(session);
        LoggingUtil.log(Level.INFO, LOGGING_KEY, "handleBinaryMessage", String.format("newBinaryMessageFromUser(%d)", userId));

        SaigonParkingMessage.Builder messageBuilder = SaigonParkingMessage.newBuilder()
                .mergeFrom(message.getPayload().array());

        try {
            if (messageBuilder.getReceiverId() != 0) {

                /* receiver's id != 0 --> not send to system --> forward to receiver */
                messagingService.prePublishMessageToQueue(messageBuilder, session);
                messagingService.publishMessageToQueue(messageBuilder.build());

            } else {
                /* receiver's id == 0 --> send to system --> not forward to receiver */
                contactService.handleMessageSendToSystem(messageBuilder.build(), session);
            }
        } catch (StatusRuntimeException exception) {

            ErrorContent content = ErrorContent.newBuilder()
                    .setInternalErrorCode(exception.getStatus().getDescription())
                    .build();

            session.sendMessage(new BinaryMessage(messageBuilder
                    .setSenderId(0)
                    .setReceiverId(userId)
                    .setClassification(SYSTEM_MESSAGE)
                    .setType(ERROR)
                    .setContent(content.toByteString())
                    .build()
                    .toByteArray()));
        }
    }
}

// Node: repos/cloned_ms_repos/saigonparking/service/contact-service/src/main/java/com/bht/saigonparking/service/contact/handler/WebSocketBinaryMessageHandler.java:WebSocketBinaryMessageHandler.<init>
// Node: afterConnectionEstablished
// Node: addNewUserSession
// Node: setNotification
// Node: afterConnectionClosed
// Node: removeUserSession
// Node: handleTransportError
// Node: handleBinaryMessage
// Node: newBinaryMessageFromUser
// Node: getPayload
// Node: array
// Node: setInternalErrorCode
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

// Node: getAttributes
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

// Node: repos/cloned_ms_repos/saigonparking/service/contact-service/src/main/java/com/bht/saigonparking/service/contact/handler/WebSocketTextMessageHandler.java:WebSocketTextMessageHandler.<init>
// Node: TextMessage
// Node: handleTextMessage
// Node: newTextMessageFromUser
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

// Node: runTest
// Node: testAuthWithWebSocketUri
// Node: testAuthWithWebSocketWebUri
// Node: testNewSocketLibrary
// Node: sleep
// Node: println
// Node: setInformation
// Node: WebSocketHttpHeaders
// Node: singletonList
// Node: StandardWebSocketClient
// Node: doHandshake
// Node: testSocketAsEmployee
// Node: testSocketAsCustomer
// Node: WebSocketFactory
// Node: createSocket
// Node: addHeader
// Node: addListener
// Node: WebSocketAdapter
// Node: onBinaryMessage
// Node: connect
// Node: setSender
// Node: setMessage
// Node: setAmountOfParkingHour
// Node: setCustomerName
// Node: setCustomerLicense
// Node: sendBinary
// Node: disconnect
package com.bht.saigonparking.emulator.configuration;

import org.springframework.context.ApplicationContext;
import org.springframework.context.ApplicationContextAware;
import org.springframework.lang.NonNull;
import org.springframework.stereotype.Component;

/**
 *
 * @author bht
 */
@Component
public final class SpringApplicationContext implements ApplicationContextAware {

    private static ApplicationContext context;

    /**
     * get bean created before by app static context
     * @param <T> any object has been injected before
     * @return Bean of a specific class
     */
    public static <T> T getBean(Class<T> beanClass) {
        return context.getBean(beanClass);
    }

    /**
     * used by Spring !!!!
     * please don't use it
     */
    @Override
    public synchronized void setApplicationContext(@NonNull ApplicationContext applicationContext) {
        context = applicationContext;
    }
}

package com.bht.saigonparking.emulator.handler;

import java.util.ArrayList;
import java.util.List;

import org.apache.logging.log4j.Level;
import org.springframework.lang.NonNull;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.PongMessage;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import com.bht.saigonparking.emulator.util.LoggingUtil;

import lombok.Getter;

/**
 *
 * @author bht
 */
@Component
public final class WebSocketHandler extends TextWebSocketHandler {

    private static final String LOGGING_KEY = "WebSocketHandler";

    @Getter
    private final List<WebSocketSession> sessionList = new ArrayList<>();

    @Override
    public void afterConnectionEstablished(@NonNull WebSocketSession session) throws Exception {
        super.afterConnectionEstablished(session);
        LoggingUtil.log(Level.INFO, LOGGING_KEY, "afterConnectionEstablished", session.getAttributes().toString());
        session.sendMessage(new TextMessage("Hello Server"));
    }

    @Override
    public void afterConnectionClosed(@NonNull WebSocketSession session, @NonNull CloseStatus status) throws Exception {
        super.afterConnectionClosed(session, status);
        LoggingUtil.log(Level.INFO, LOGGING_KEY, "afterConnectionClosed", session.getAttributes().toString());
    }

    @Override
    protected void handleTextMessage(@NonNull WebSocketSession session, @NonNull TextMessage message) throws Exception {
        super.handleTextMessage(session, message);
        LoggingUtil.log(Level.INFO, LOGGING_KEY, "handleTextMessage", message.getPayload());
    }

    @Override
    protected void handlePongMessage(@NonNull WebSocketSession session, @NonNull PongMessage message) throws Exception {
        super.handlePongMessage(session, message);
        LoggingUtil.log(Level.INFO, LOGGING_KEY, "handlePongMessage", message.getPayload().toString());
    }

    @Override
    public void handleTransportError(@NonNull WebSocketSession session, @NonNull Throwable exception) throws Exception {
        super.handleTransportError(session, exception);
        LoggingUtil.log(Level.INFO, LOGGING_KEY, "handleTransportError", session.getAttributes().toString());
    }
}

// Node: repos/cloned_ms_repos/saigonparking/emulator/src/main/java/com/bht/saigonparking/emulator/handler/WebSocketHandler.java:WebSocketHandler.<init>
// Node: handlePongMessage
