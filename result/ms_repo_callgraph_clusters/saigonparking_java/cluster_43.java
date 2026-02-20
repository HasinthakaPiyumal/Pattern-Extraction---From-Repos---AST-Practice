// Cluster 43

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

// Node: configure
// Node: sources
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

