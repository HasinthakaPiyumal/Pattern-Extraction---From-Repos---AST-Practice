// Cluster 11

package com.bht.saigonparking.common.annotation;

import static java.lang.annotation.ElementType.*;

import java.lang.annotation.Documented;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

import javax.validation.Constraint;
import javax.validation.Payload;
import javax.validation.constraints.NotEmpty;

import com.bht.saigonparking.common.validator.UuidStringValidator;

/**
 *
 * @author bht
 */
@NotEmpty
@Documented
@Retention(RetentionPolicy.RUNTIME)
@Constraint(validatedBy = UuidStringValidator.class)
@Target({FIELD, METHOD, ANNOTATION_TYPE, CONSTRUCTOR, PARAMETER})
public @interface UuidStringValidation {

    String message() default "UUID string is in wrong format !";

    Class<?>[] groups() default {};

    Class<? extends Payload>[] payload() default {};
}

// Node: repos/cloned_ms_repos/saigonparking/common/src/main/java/com/bht/saigonparking/common/annotation/UuidStringValidation.java:UuidStringValidation.<init>
// Node: Retention
// Node: Constraint
// Node: Target
// Node: message
// Node: groups
// Node: payload
package com.bht.saigonparking.common.annotation;

import java.lang.annotation.ElementType;
import java.lang.annotation.Inherited;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

import org.springframework.stereotype.Component;

/**
 *
 * This annotation using only for abstract class or interface
 * which children (who extends this abstract class or implements this interface)
 * need to be component or need to be injected on application starts !
 *
 * <code>@Component</code> annotation of spring,
 * marks that this class will be injected
 *
 * <code>@Inherited</code> annotation of java lang,
 * marks that the above annotation will be inherited into children: @Component
 *
 * @author bht
 */
@Component
@Inherited
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
public @interface InheritedComponent {
}

// Node: repos/cloned_ms_repos/saigonparking/common/src/main/java/com/bht/saigonparking/common/annotation/InheritedComponent.java:or.<init>
// Node: children
package com.bht.saigonparking.common.annotation;

import static java.lang.annotation.ElementType.*;
import static java.lang.annotation.RetentionPolicy.RUNTIME;

import java.lang.annotation.Documented;
import java.lang.annotation.Retention;
import java.lang.annotation.Target;

import javax.validation.Constraint;
import javax.validation.Payload;
import javax.validation.constraints.Email;
import javax.validation.constraints.Pattern;

/**
 *
 * @author bht
 */
@Email
@Documented
@Retention(RUNTIME)
@Target({METHOD, FIELD, ANNOTATION_TYPE})
@Pattern(regexp = ".+@.+\\..+")
@Constraint(validatedBy = {})
public @interface EmailValidation {

    String message() default "Invalid email address";

    Class<?>[] groups() default {};

    Class<? extends Payload>[] payload() default {};
}

// Node: repos/cloned_ms_repos/saigonparking/common/src/main/java/com/bht/saigonparking/common/annotation/EmailValidation.java:EmailValidation.<init>
// Node: Pattern
package com.bht.saigonparking.common.annotation;

import static java.lang.annotation.ElementType.*;

import java.lang.annotation.Documented;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

import javax.validation.Constraint;
import javax.validation.Payload;
import javax.validation.constraints.NotEmpty;

import com.bht.saigonparking.common.validator.LicensePlateValidator;

/**
 *
 * @author bht
 */
@NotEmpty
@Documented
@Retention(RetentionPolicy.RUNTIME)
@Constraint(validatedBy = LicensePlateValidator.class)
@Target({FIELD, METHOD, ANNOTATION_TYPE, CONSTRUCTOR, PARAMETER})
public @interface LicensePlateValidation {

    String message() default "Number license plate is in wrong format !";

    Class<?>[] groups() default {};

    Class<? extends Payload>[] payload() default {};
}

// Node: repos/cloned_ms_repos/saigonparking/common/src/main/java/com/bht/saigonparking/common/annotation/LicensePlateValidation.java:LicensePlateValidation.<init>
package com.bht.saigonparking.service.parkinglot.annotation;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

import javax.validation.Constraint;
import javax.validation.Payload;

import com.bht.saigonparking.service.parkinglot.annotation.impl.CapacityValidator;

/**
 *
 * @author bht
 */
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@Constraint(validatedBy = CapacityValidator.class)
public @interface CapacityValidation {

    String message() default "Availability cannot be larger than Capacity !";

    Class<?>[] groups() default {};

    Class<? extends Payload>[] payload() default {};
}

// Node: repos/cloned_ms_repos/saigonparking/service/parkinglot-service/src/main/java/com/bht/saigonparking/service/parkinglot/annotation/CapacityValidation.java:CapacityValidation.<init>
package com.bht.saigonparking.service.parkinglot.annotation;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

import javax.validation.Constraint;
import javax.validation.Payload;

import com.bht.saigonparking.service.parkinglot.annotation.impl.TimeFlowValidator;

/**
 *
 * @author bht
 */
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@Constraint(validatedBy = TimeFlowValidator.class)
public @interface TimeFlowValidation {

    String message() default "Closing hour cannot be earlier than opening hour !";

    Class<?>[] groups() default {};

    Class<? extends Payload>[] payload() default {};
}

// Node: repos/cloned_ms_repos/saigonparking/service/parkinglot-service/src/main/java/com/bht/saigonparking/service/parkinglot/annotation/TimeFlowValidation.java:TimeFlowValidation.<init>
