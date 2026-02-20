// Cluster 14

package com.bht.saigonparking.common.base;

import javax.persistence.Column;
import javax.persistence.GeneratedValue;
import javax.persistence.GenerationType;
import javax.persistence.Id;
import javax.persistence.MappedSuperclass;
import javax.persistence.Version;

import lombok.AllArgsConstructor;
import lombok.EqualsAndHashCode;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import lombok.ToString;
import lombok.experimental.SuperBuilder;

/**
 *
 * Saigon Parking Project Base Entity
 *
 * Mutual fields of each entity is declared in this abstract class, include:
 *      + id: unique id, primary key of each entity
 *      + version: version of each entity, for concurrent control
 *
 * Remember to annotate this abstract class with <code>@MappedSuperclass</code>
 * in order to inherit all of these mutual fields
 * into each child entity, which is annotated with <code>@Entity</code>
 *
 * Also remember to call super on toString(), equals(), hashCode() on each child !!!!!
 *
 * All mutual fields will be compare as equals() and hashCode(), except id and version
 * because id and version is managed by Hibernate, furthermore id is generated value !
 *
 * @author bht
 */
@Getter
@Setter
@ToString
@SuperBuilder
@EqualsAndHashCode
@NoArgsConstructor
@AllArgsConstructor
@MappedSuperclass
public abstract class BaseEntity {

    @Id
    @Column(name = "[ID]")
    @EqualsAndHashCode.Exclude
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    protected Long id;

    @Version
    @EqualsAndHashCode.Exclude
    protected Long version;
}

// Node: repos/cloned_ms_repos/saigonparking/common/src/main/java/com/bht/saigonparking/common/base/BaseEntity.java:with.<init>
// Node: hashCode
// Node: Column
// Node: GeneratedValue
package com.bht.saigonparking.service.auth.entity;

import java.util.UUID;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.Id;
import javax.persistence.Table;
import javax.persistence.Version;

import org.hibernate.annotations.NaturalId;
import org.hibernate.annotations.NaturalIdCache;
import org.hibernate.annotations.SelectBeforeUpdate;
import org.hibernate.annotations.Type;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.EqualsAndHashCode;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import lombok.ToString;

/**
 *
 * @author bht
 */
@Entity
@Getter
@Setter
@Builder
@ToString
@NaturalIdCache
@EqualsAndHashCode
@NoArgsConstructor
@AllArgsConstructor
@SelectBeforeUpdate
@Table(name = "[USER_TOKEN]")
public final class UserTokenEntity {

    @Id
    @Column(name = "[USER_ID]")
    private Long userId;

    @Type(type = "uuid-char")
    @NaturalId(mutable = true)
    @Column(name = "[TOKEN_ID]", unique = true, nullable = false, columnDefinition = "UNIQUEIDENTIFIER")
    private UUID tokenId;

    @Version
    @EqualsAndHashCode.Exclude
    private Long version;
}

// Node: repos/cloned_ms_repos/saigonparking/service/auth-service/src/main/java/com/bht/saigonparking/service/auth/entity/UserTokenEntity.java:UserTokenEntity.<init>
// Node: Table
// Node: Type
// Node: NaturalId
package com.bht.saigonparking.service.parkinglot.entity;

import java.sql.Time;
import java.util.Set;

import javax.persistence.CascadeType;
import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.JoinColumn;
import javax.persistence.ManyToOne;
import javax.persistence.OneToMany;
import javax.persistence.OneToOne;
import javax.persistence.Table;

import org.hibernate.annotations.ColumnDefault;
import org.hibernate.annotations.SelectBeforeUpdate;

import com.bht.saigonparking.common.base.BaseEntity;
import com.bht.saigonparking.service.parkinglot.annotation.TimeFlowValidation;

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
@TimeFlowValidation
@Table(name = "[PARKING_LOT]")
public final class ParkingLotEntity extends BaseEntity {

    @ManyToOne(optional = false)
    @JoinColumn(name = "[PARKING_LOT_TYPE_ID]", referencedColumnName = "[ID]", nullable = false, updatable = false)
    private ParkingLotTypeEntity parkingLotTypeEntity;

    @Column(name = "[LATITUDE]", nullable = false)
    private Double latitude;

    @Column(name = "[LONGITUDE]", nullable = false)
    private Double longitude;

    @Column(name = "[OPENING_HOUR]", nullable = false)
    private Time openingHour;

    @Column(name = "[CLOSING_HOUR]", nullable = false)
    private Time closingHour;

    @ColumnDefault("true")
    @Column(name = "[IS_AVAILABLE]")
    private Boolean isAvailable;

    @OneToOne(mappedBy = "parkingLotEntity", cascade = CascadeType.ALL, orphanRemoval = true)
    private ParkingLotLimitEntity parkingLotLimitEntity;

    @OneToOne(mappedBy = "parkingLotEntity", cascade = CascadeType.ALL, orphanRemoval = true)
    private ParkingLotInformationEntity parkingLotInformationEntity;

    @ToString.Exclude
    @EqualsAndHashCode.Exclude
    @OneToMany(mappedBy = "parkingLotEntity", cascade = CascadeType.ALL, orphanRemoval = true)
    private Set<ParkingLotUnitEntity> parkingLotUnitEntitySet;

    @ToString.Exclude
    @EqualsAndHashCode.Exclude
    @OneToMany(mappedBy = "parkingLotEntity", cascade = CascadeType.ALL, orphanRemoval = true)
    private Set<ParkingLotEmployeeEntity> parkingLotEmployeeEntitySet;
}

// Node: repos/cloned_ms_repos/saigonparking/service/parkinglot-service/src/main/java/com/bht/saigonparking/service/parkinglot/entity/ParkingLotEntity.java:ParkingLotEntity.<init>
// Node: ToString
// Node: EqualsAndHashCode
// Node: ManyToOne
// Node: JoinColumn
// Node: ColumnDefault
// Node: OneToOne
// Node: OneToMany
package com.bht.saigonparking.service.parkinglot.entity;

import java.util.Set;

import javax.persistence.CascadeType;
import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.OneToMany;
import javax.persistence.Table;

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
@Table(name = "[PARKING_LOT_TYPE]")
public final class ParkingLotTypeEntity extends BaseEntity {

    @Column(name = "[TYPE]", nullable = false, unique = true, updatable = false)
    private String type;

    @ToString.Exclude
    @EqualsAndHashCode.Exclude
    @OneToMany(mappedBy = "parkingLotTypeEntity", cascade = CascadeType.ALL, orphanRemoval = true)
    private Set<ParkingLotEntity> parkingLotEntitySet;
}

// Node: repos/cloned_ms_repos/saigonparking/service/parkinglot-service/src/main/java/com/bht/saigonparking/service/parkinglot/entity/ParkingLotTypeEntity.java:ParkingLotTypeEntity.<init>
package com.bht.saigonparking.service.parkinglot.entity;

import java.sql.Timestamp;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.JoinColumn;
import javax.persistence.ManyToOne;
import javax.persistence.Table;

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
@Table(name = "[PARKING_LOT_UNIT]")
public final class ParkingLotUnitEntity extends BaseEntity {

    @ManyToOne(optional = false)
    @JoinColumn(name = "[PARKING_LOT_ID]", referencedColumnName = "[ID]", nullable = false)
    private ParkingLotEntity parkingLotEntity;

    @Column(name = "[LOWER_BOUND_HOUR]", nullable = false)
    private Short lowerBoundHour;

    @Column(name = "[UPPER_BOUND_HOUR]", nullable = false)
    private Short upperBoundHour;

    @Column(name = "[UNIT_PRICE_PER_HOUR]", nullable = false)
    private Integer unitPricePerHour;

    @EqualsAndHashCode.Exclude
    @Column(name = "[LAST_UPDATED]")
    private Timestamp lastUpdated;
}

// Node: repos/cloned_ms_repos/saigonparking/service/parkinglot-service/src/main/java/com/bht/saigonparking/service/parkinglot/entity/ParkingLotUnitEntity.java:ParkingLotUnitEntity.<init>
package com.bht.saigonparking.service.parkinglot.entity;

import java.sql.Timestamp;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.Table;

import org.hibernate.annotations.ColumnDefault;
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
@Table(name = "[PARKING_LOT_SUGGESTION]")
public final class ParkingLotSuggestionEntity extends BaseEntity {

    @Column(name = "[NAME]", nullable = false)
    private String parkingLotName;

    @Column(name = "[ADDRESS]", nullable = false)
    private String parkingLotAddress;

    @Column(name = "[LATITUDE]", nullable = false)
    private Double latitude;

    @Column(name = "[LONGITUDE]", nullable = false)
    private Double longitude;

    @ColumnDefault("false")
    @Column(name = "[IS_HANDLED]")
    private Boolean isHandled;

    @Column(name = "[CUSTOMER_ID]", nullable = false)
    private Long customerId;

    @EqualsAndHashCode.Exclude
    @Column(name = "[LAST_UPDATED]")
    private Timestamp lastUpdated;
}

// Node: repos/cloned_ms_repos/saigonparking/service/parkinglot-service/src/main/java/com/bht/saigonparking/service/parkinglot/entity/ParkingLotSuggestionEntity.java:ParkingLotSuggestionEntity.<init>
package com.bht.saigonparking.service.parkinglot.entity;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.JoinColumn;
import javax.persistence.MapsId;
import javax.persistence.OneToOne;
import javax.persistence.Table;

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
@Table(name = "[PARKING_LOT_INFORMATION]")
public final class ParkingLotInformationEntity extends BaseEntity {

    @Column(name = "[NAME]", nullable = false)
    private String name;

    @Column(name = "[ADDRESS]", nullable = false)
    private String address;

    @Column(name = "[PHONE]")
    private String phone;

    @MapsId
    @ToString.Exclude
    @EqualsAndHashCode.Exclude
    @OneToOne(optional = false)
    @JoinColumn(name = "[ID]", unique = true)
    private ParkingLotEntity parkingLotEntity;
}

// Node: repos/cloned_ms_repos/saigonparking/service/parkinglot-service/src/main/java/com/bht/saigonparking/service/parkinglot/entity/ParkingLotInformationEntity.java:ParkingLotInformationEntity.<init>
package com.bht.saigonparking.service.parkinglot.entity;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.JoinColumn;
import javax.persistence.MapsId;
import javax.persistence.OneToOne;
import javax.persistence.Table;

import org.hibernate.annotations.ColumnDefault;
import org.hibernate.annotations.SelectBeforeUpdate;

import com.bht.saigonparking.common.base.BaseEntity;
import com.bht.saigonparking.service.parkinglot.annotation.CapacityValidation;

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
@CapacityValidation
@Table(name = "[PARKING_LOT_LIMIT]")
public final class ParkingLotLimitEntity extends BaseEntity {

    @ColumnDefault("0")
    @Column(name = "[AVAILABILITY]")
    private Short availableSlot;

    @ColumnDefault("0")
    @Column(name = "[CAPACITY]")
    private Short totalSlot;

    @MapsId
    @ToString.Exclude
    @EqualsAndHashCode.Exclude
    @OneToOne(optional = false)
    @JoinColumn(name = "[ID]", unique = true)
    private ParkingLotEntity parkingLotEntity;
}

// Node: repos/cloned_ms_repos/saigonparking/service/parkinglot-service/src/main/java/com/bht/saigonparking/service/parkinglot/entity/ParkingLotLimitEntity.java:ParkingLotLimitEntity.<init>
package com.bht.saigonparking.service.parkinglot.entity;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.JoinColumn;
import javax.persistence.ManyToOne;
import javax.persistence.Table;

import org.hibernate.annotations.NaturalId;
import org.hibernate.annotations.NaturalIdCache;
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
@NaturalIdCache
@ToString(callSuper = true)
@EqualsAndHashCode(callSuper = true)
@NoArgsConstructor
@AllArgsConstructor
@SelectBeforeUpdate
@Table(name = "[PARKING_LOT_EMPLOYEE]")
public final class ParkingLotEmployeeEntity extends BaseEntity {

    @ManyToOne(optional = false)
    @JoinColumn(name = "[PARKING_LOT_ID]", referencedColumnName = "[ID]", nullable = false, updatable = false)
    private ParkingLotEntity parkingLotEntity;

    @NaturalId
    @Column(name = "[USER_ID]", nullable = false, updatable = false, unique = true)
    private Long userId;
}

// Node: repos/cloned_ms_repos/saigonparking/service/parkinglot-service/src/main/java/com/bht/saigonparking/service/parkinglot/entity/ParkingLotEmployeeEntity.java:ParkingLotEmployeeEntity.<init>
package com.bht.saigonparking.service.user.entity;

import java.util.Set;

import javax.persistence.CascadeType;
import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.OneToMany;
import javax.persistence.Table;

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
@Table(name = "[USER_ROLE]")
public final class UserRoleEntity extends BaseEntity {

    @Column(name = "[ROLE]", nullable = false, unique = true, updatable = false)
    private String role;

    @ToString.Exclude
    @EqualsAndHashCode.Exclude
    @OneToMany(mappedBy = "userRoleEntity", cascade = CascadeType.ALL, orphanRemoval = true)
    private Set<UserEntity> userEntitySet;
}

// Node: repos/cloned_ms_repos/saigonparking/service/user-service/src/main/java/com/bht/saigonparking/service/user/entity/UserRoleEntity.java:UserRoleEntity.<init>
package com.bht.saigonparking.service.user.entity;

import java.sql.Timestamp;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.PrimaryKeyJoinColumn;
import javax.persistence.Table;

import org.hibernate.annotations.SelectBeforeUpdate;

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
@Table(name = "[CUSTOMER]")
@PrimaryKeyJoinColumn(name = "[ID]")
public final class CustomerEntity extends UserEntity {

    @Column(name = "[FIRST_NAME]", nullable = false)
    private String firstName;

    @Column(name = "[LAST_NAME]", nullable = false)
    private String lastName;

    @Column(name = "[PHONE]", nullable = false)
    private String phone;

    @EqualsAndHashCode.Exclude
    @Column(name = "[LAST_UPDATED]")
    private Timestamp lastUpdated;
}

// Node: repos/cloned_ms_repos/saigonparking/service/user-service/src/main/java/com/bht/saigonparking/service/user/entity/CustomerEntity.java:CustomerEntity.<init>
// Node: PrimaryKeyJoinColumn
package com.bht.saigonparking.service.user.entity;

import java.sql.Timestamp;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.Inheritance;
import javax.persistence.InheritanceType;
import javax.persistence.JoinColumn;
import javax.persistence.ManyToOne;
import javax.persistence.Table;

import org.hibernate.annotations.ColumnDefault;
import org.hibernate.annotations.NaturalId;
import org.hibernate.annotations.NaturalIdCache;
import org.hibernate.annotations.SelectBeforeUpdate;

import com.bht.saigonparking.common.annotation.EmailValidation;
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
@Table(name = "[USER]")
@Inheritance(strategy = InheritanceType.JOINED)
public class UserEntity extends BaseEntity {

    @ManyToOne(optional = false)
    @JoinColumn(name = "[ROLE_ID]", referencedColumnName = "[ID]", nullable = false, updatable = false)
    protected UserRoleEntity userRoleEntity;

    @NaturalId
    @Column(name = "[USERNAME]", nullable = false, unique = true, updatable = false)
    protected String username;

    @Column(name = "[PASSWORD]", nullable = false)
    protected String password;

    @EmailValidation
    @Column(name = "[EMAIL]", nullable = false, unique = true)
    protected String email;

    @ColumnDefault("false")
    @Column(name = "[IS_ACTIVATED]")
    protected Boolean isActivated;

    @EqualsAndHashCode.Exclude
    @Column(name = "[LAST_SIGN_IN]")
    protected Timestamp lastSignIn;
}

// Node: repos/cloned_ms_repos/saigonparking/service/user-service/src/main/java/com/bht/saigonparking/service/user/entity/UserEntity.java:UserEntity.<init>
// Node: Inheritance
package com.bht.saigonparking.service.booking.entity;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.Table;

import org.hibernate.annotations.ColumnDefault;
import org.hibernate.annotations.NaturalId;
import org.hibernate.annotations.NaturalIdCache;
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
@NaturalIdCache
@ToString(callSuper = true)
@EqualsAndHashCode(callSuper = true)
@NoArgsConstructor
@AllArgsConstructor
@SelectBeforeUpdate
@Table(name = "[BOOKING_STATISTIC]")
public final class BookingStatisticEntity extends BaseEntity {

    @NaturalId
    @Column(name = "[PARKING_LOT_ID]", nullable = false, unique = true)
    private Long parkingLotId;

    @ColumnDefault("0")
    @Column(name = "[RATING_AVERAGE]", updatable = false)
    private Double ratingAverage;

    @ColumnDefault("0")
    @Column(name = "[NUMBER_OF_RATING]", updatable = false)
    private Long nRating;

    @ColumnDefault("0")
    @Column(name = "[NUMBER_OF_BOOKING]", updatable = false)
    private Long nBooking;
}

// Node: repos/cloned_ms_repos/saigonparking/service/booking-service/src/main/java/com/bht/saigonparking/service/booking/entity/BookingStatisticEntity.java:BookingStatisticEntity.<init>
package com.bht.saigonparking.service.booking.entity;

import java.util.Set;

import javax.persistence.CascadeType;
import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.OneToMany;
import javax.persistence.Table;

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
@Table(name = "[BOOKING_STATUS]")
public final class BookingStatusEntity extends BaseEntity {

    @Column(name = "[STATUS]", nullable = false, unique = true, insertable = false, updatable = false)
    private String status;

    @ToString.Exclude
    @EqualsAndHashCode.Exclude
    @OneToMany(mappedBy = "bookingStatusEntity", cascade = CascadeType.ALL, orphanRemoval = true)
    private Set<BookingEntity> bookingEntitySet;

    @ToString.Exclude
    @EqualsAndHashCode.Exclude
    @OneToMany(mappedBy = "bookingStatusEntity", cascade = CascadeType.ALL, orphanRemoval = true)
    private Set<BookingHistoryEntity> bookingHistoryEntitySet;
}

// Node: repos/cloned_ms_repos/saigonparking/service/booking-service/src/main/java/com/bht/saigonparking/service/booking/entity/BookingStatusEntity.java:BookingStatusEntity.<init>
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

// Node: repos/cloned_ms_repos/saigonparking/service/booking-service/src/main/java/com/bht/saigonparking/service/booking/entity/BookingEntity.java:BookingEntity.<init>
// Node: SortByCreatedAt
// Node: thenComparing
// Node: SortById
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

// Node: repos/cloned_ms_repos/saigonparking/service/booking-service/src/main/java/com/bht/saigonparking/service/booking/entity/BookingHistoryEntity.java:BookingHistoryEntity.<init>
// Node: SortByLastUpdated
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

// Node: repos/cloned_ms_repos/saigonparking/service/booking-service/src/main/java/com/bht/saigonparking/service/booking/entity/BookingRatingEntity.java:BookingRatingEntity.<init>
