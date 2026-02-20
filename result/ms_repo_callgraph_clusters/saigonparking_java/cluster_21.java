// Cluster 21

// Node: getName
package com.bht.saigonparking.common.validator;

import javax.validation.ConstraintValidator;
import javax.validation.ConstraintValidatorContext;

import com.bht.saigonparking.common.annotation.LicensePlateValidation;

/**
 *
 * @author bht
 */
public final class LicensePlateValidator implements ConstraintValidator<LicensePlateValidation, String> {

    @Override
    public boolean isValid(String numberLicensePlate, ConstraintValidatorContext constraintValidatorContext) {
        return numberLicensePlate
                .replaceAll("\\s+|\\.+", "")                 // remove all space and dot characters exist in string
                .matches("^[0-9]{1,2}[A-Za-z][0-9]?-[0-9]{4,5}$");      // example: 59H1-76217, 54L6-2908, 51B-1234, 86B-56789
    }
}

// Node: isValid
// Node: replaceAll
// Node: matches
package com.bht.saigonparking.common.validator;

import javax.validation.ConstraintValidator;
import javax.validation.ConstraintValidatorContext;

import com.bht.saigonparking.common.annotation.UuidStringValidation;

/**
 *
 * @author bht
 */
public final class UuidStringValidator implements ConstraintValidator<UuidStringValidation, String> {

    @Override
    public boolean isValid(String uuidString, ConstraintValidatorContext constraintValidatorContext) {
        return uuidString.matches("^[A-Za-z0-9]{8}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{12}$");
    }
}

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

// Node: postProcessBeforeInitialization
// Node: getPackage
// Node: startsWith
// Node: postProcessBeforeDestruction
package com.bht.saigonparking.service.parkinglot.annotation.impl;

import javax.validation.ConstraintValidator;
import javax.validation.ConstraintValidatorContext;

import com.bht.saigonparking.service.parkinglot.annotation.TimeFlowValidation;
import com.bht.saigonparking.service.parkinglot.entity.ParkingLotEntity;

/**
 *
 * @author bht
 */
public final class TimeFlowValidator implements ConstraintValidator<TimeFlowValidation, ParkingLotEntity> {

    @Override
    public boolean isValid(ParkingLotEntity parkingLotEntity, ConstraintValidatorContext constraintValidatorContext) {
        return parkingLotEntity.getClosingHour().after(parkingLotEntity.getOpeningHour());
    }
}

// Node: getClosingHour
// Node: after
// Node: getOpeningHour
package com.bht.saigonparking.service.parkinglot.annotation.impl;

import javax.validation.ConstraintValidator;
import javax.validation.ConstraintValidatorContext;

import com.bht.saigonparking.service.parkinglot.annotation.CapacityValidation;
import com.bht.saigonparking.service.parkinglot.entity.ParkingLotLimitEntity;

/**
 *
 * @author bht
 */
public final class CapacityValidator implements ConstraintValidator<CapacityValidation, ParkingLotLimitEntity> {

    @Override
    public boolean isValid(ParkingLotLimitEntity parkingLotLimitEntity, ConstraintValidatorContext constraintValidatorContext) {
        return parkingLotLimitEntity.getAvailableSlot().compareTo((short) 0) >= 0 &&
                parkingLotLimitEntity.getAvailableSlot().compareTo(parkingLotLimitEntity.getTotalSlot()) <= 0;
    }
}

// Node: getAvailableSlot
// Node: compareTo
// Node: getTotalSlot
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

// Node: toParkingLotEntity
// Node: getParkingLotLimitEntity
// Node: getParkingLotInformationEntity
// Node: setTotalSlot
// Node: setAvailableSlot
// Node: setName
// Node: setAddress
// Node: getAddress
// Node: ParkingLotEntity
// Node: setParkingLotUnitEntitySet
// Node: emptySet
// Node: setParkingLotEmployeeEntitySet
// Node: setParkingLotTypeEntity
// Node: setLatitude
// Node: setLongitude
// Node: setOpeningHour
// Node: setClosingHour
package com.bht.saigonparking.service.parkinglot.mapper;

import javax.validation.constraints.NotNull;

import com.bht.saigonparking.api.grpc.parkinglot.ParkingLot;
import com.bht.saigonparking.service.parkinglot.entity.ParkingLotEntity;

/**
 *
 * @author bht
 */
public interface ParkingLotMapperExt {

    ParkingLotEntity toParkingLotEntity(@NotNull ParkingLot parkingLot, boolean isAboutToCreate);
}

// Node: repos/cloned_ms_repos/saigonparking/service/parkinglot-service/src/main/java/com/bht/saigonparking/service/parkinglot/mapper/ParkingLotMapperExt.java:ParkingLotMapperExt.<init>
package com.bht.saigonparking.service.booking.entity;

import java.sql.Timestamp;
import java.util.Comparator;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

import javax.persistence.CascadeType;
import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.JoinColumn;
import javax.persistence.ManyToOne;
import javax.persistence.OneToMany;
import javax.persistence.OneToOne;
import javax.persistence.Table;

import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.NaturalId;
import org.hibernate.annotations.NaturalIdCache;
import org.hibernate.annotations.SelectBeforeUpdate;
import org.hibernate.annotations.Type;

import com.bht.saigonparking.common.annotation.LicensePlateValidation;
import com.bht.saigonparking.common.base.BaseEntity;

import lombok.AllArgsConstructor;
import lombok.EqualsAndHashCode;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import lombok.ToString;
import lombok.experimental.SuperBuilder;

/**
 *
 * @author bht
 */
@Entity
@Getter
@Setter
@SuperBuilder
@NaturalIdCache
@ToString(callSuper = true)
@EqualsAndHashCode(callSuper = true)
@NoArgsConstructor
@AllArgsConstructor
@SelectBeforeUpdate
@Table(name = "[BOOKING]")
public final class BookingEntity extends BaseEntity {

    public static final Comparator<Map.Entry<BookingEntity, String>> SORT_BY_CREATED_AT_THEN_BY_BOOKING_ID = new SortByCreatedAt().thenComparing(new SortById());

    @NaturalId
    @Type(type = "uuid-char")
    @Column(name = "[UUID]", nullable = false, unique = true, updatable = false, columnDefinition = "UNIQUEIDENTIFIER")
    private UUID uuid;

    @Column(name = "[PARKING_LOT_ID]", nullable = false)
    private Long parkingLotId;

    @Column(name = "[CUSTOMER_ID]", nullable = false)
    private Long customerId;

    @LicensePlateValidation
    @Column(name = "[CUSTOMER_LICENSE_PLATE]", nullable = false)
    private String customerLicensePlate;

    @Column(name = "[IS_FINISHED]", updatable = false)
    private Boolean isFinished;

    @Column(name = "[IS_RATED]", updatable = false)
    private Boolean isRated;

    @CreationTimestamp
    @EqualsAndHashCode.Exclude
    @Column(name = "[CREATED_AT]", nullable = false, updatable = false)
    private Timestamp createdAt;

    @ManyToOne(optional = false)
    @JoinColumn(name = "[LATEST_STATUS_ID]", referencedColumnName = "[ID]", nullable = false, updatable = false)
    private BookingStatusEntity bookingStatusEntity;

    @OneToOne(mappedBy = "bookingEntity", cascade = CascadeType.ALL, orphanRemoval = true)
    private BookingRatingEntity bookingRatingEntity;

    @ToString.Exclude
    @EqualsAndHashCode.Exclude
    @OneToMany(mappedBy = "bookingEntity", cascade = CascadeType.ALL, orphanRemoval = true)
    private Set<BookingHistoryEntity> bookingHistoryEntitySet;

    @NoArgsConstructor
    private static final class SortByCreatedAt implements Comparator<Map.Entry<BookingEntity, String>> {
        @Override
        public int compare(Map.Entry<BookingEntity, String> bookingEntry1, Map.Entry<BookingEntity, String> bookingEntry2) {
            return bookingEntry2.getKey().createdAt.compareTo(bookingEntry1.getKey().createdAt);
        }
    }

    @NoArgsConstructor
    private static final class SortById implements Comparator<Map.Entry<BookingEntity, String>> {
        @Override
        public int compare(Map.Entry<BookingEntity, String> bookingEntry1, Map.Entry<BookingEntity, String> bookingEntry2) {
            return bookingEntry2.getKey().id.compareTo(bookingEntry1.getKey().id);
        }
    }
}

// Node: compare
package com.bht.saigonparking.service.booking.entity;

import java.sql.Timestamp;
import java.util.Comparator;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.JoinColumn;
import javax.persistence.ManyToOne;
import javax.persistence.Table;

import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.SelectBeforeUpdate;

import com.bht.saigonparking.common.base.BaseEntity;

import lombok.AllArgsConstructor;
import lombok.EqualsAndHashCode;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import lombok.ToString;
import lombok.experimental.SuperBuilder;

/**
 *
 * @author bht
 */
@Entity
@Getter
@Setter
@SuperBuilder
@ToString(callSuper = true)
@EqualsAndHashCode(callSuper = true)
@NoArgsConstructor
@AllArgsConstructor
@SelectBeforeUpdate
@Table(name = "[BOOKING_HISTORY]")
public final class BookingHistoryEntity extends BaseEntity {

    public static final Comparator<BookingHistoryEntity> SORT_BY_LAST_UPDATED_THEN_BY_ID =
            new SortByLastUpdated().thenComparing(new SortById());

    @ManyToOne(optional = false)
    @JoinColumn(name = "[BOOKING_ID]", referencedColumnName = "[ID]", nullable = false, updatable = false)
    private BookingEntity bookingEntity;

    @ManyToOne(optional = false)
    @JoinColumn(name = "[STATUS_ID]", referencedColumnName = "[ID]", nullable = false, updatable = false)
    private BookingStatusEntity bookingStatusEntity;

    @Column(name = "[NOTE]")
    private String note;

    @CreationTimestamp
    @EqualsAndHashCode.Exclude
    @Column(name = "[LAST_UPDATED]", nullable = false, updatable = false)
    private Timestamp lastUpdated;

    @NoArgsConstructor
    private static final class SortByLastUpdated implements Comparator<BookingHistoryEntity> {
        @Override
        public int compare(BookingHistoryEntity history1, BookingHistoryEntity history2) {
            return history2.lastUpdated.compareTo(history1.lastUpdated);
        }
    }

    @NoArgsConstructor
    private static final class SortById implements Comparator<BookingHistoryEntity> {
        @Override
        public int compare(BookingHistoryEntity history1, BookingHistoryEntity history2) {
            return history2.id.compareTo(history1.id);
        }
    }
}

package com.bht.saigonparking.service.booking.entity;

import java.sql.Timestamp;
import java.util.Comparator;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.JoinColumn;
import javax.persistence.MapsId;
import javax.persistence.OneToOne;
import javax.persistence.Table;

import org.hibernate.annotations.SelectBeforeUpdate;
import org.hibernate.annotations.UpdateTimestamp;
import org.hibernate.validator.constraints.Range;

import com.bht.saigonparking.common.base.BaseEntity;

import lombok.AllArgsConstructor;
import lombok.EqualsAndHashCode;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import lombok.ToString;
import lombok.experimental.SuperBuilder;

/**
 *
 * @author bht
 */
@Entity
@Getter
@Setter
@SuperBuilder
@ToString(callSuper = true)
@EqualsAndHashCode(callSuper = true)
@NoArgsConstructor
@AllArgsConstructor
@SelectBeforeUpdate
@Table(name = "[BOOKING_RATING]")
public final class BookingRatingEntity extends BaseEntity {

    public static final Comparator<BookingRatingEntity> SORT_BY_LAST_UPDATED_THEN_BY_ID =
            new SortByLastUpdated().thenComparing(new SortById());

    @Range(min = 1, max = 5)
    @Column(name = "[RATING]", nullable = false)
    private Short rating;

    @Column(name = "[COMMENT]")
    private String comment;

    @UpdateTimestamp
    @EqualsAndHashCode.Exclude
    @Column(name = "[LAST_UPDATED]")
    private Timestamp lastUpdated;

    @MapsId
    @ToString.Exclude
    @EqualsAndHashCode.Exclude
    @OneToOne(optional = false)
    @JoinColumn(name = "[ID]", unique = true)
    private BookingEntity bookingEntity;

    @NoArgsConstructor
    private static final class SortByLastUpdated implements Comparator<BookingRatingEntity> {
        @Override
        public int compare(BookingRatingEntity rating1, BookingRatingEntity rating2) {
            return rating2.lastUpdated.compareTo(rating1.lastUpdated);
        }
    }

    @NoArgsConstructor
    private static final class SortById implements Comparator<BookingRatingEntity> {
        @Override
        public int compare(BookingRatingEntity rating1, BookingRatingEntity rating2) {
            return rating2.id.compareTo(rating1.id);
        }
    }
}

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

