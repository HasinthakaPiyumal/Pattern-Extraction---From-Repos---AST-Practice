// Cluster 13

// Node: put
package io.javatab.microservices.core.course.web;

import io.javatab.microservices.core.course.domain.Course;
import io.javatab.microservices.core.course.domain.CourseService;
import io.javatab.util.http.NetworkUtility;
import jakarta.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

@RestController()
@RequestMapping("/api/courses")
public class CourseController {

    private final Logger logger = LoggerFactory.getLogger(CourseController.class);

    private final NetworkUtility utility;
    private CourseService courseService;

    public CourseController(NetworkUtility utility, CourseService courseService) {
        this.utility = utility;
        this.courseService = courseService;
    }

    @GetMapping
    public Iterable<Course> get() {
        logger.info("Fetching courses");
        return courseService.viewCourses();
    }

    /*
    * Make sure application is running in localhost mode to test and not in docker
    * http GET ':9001/api/courses/Microservices with Spring Boot'
    * */
    @GetMapping("/title/{title}")
    public Course getByTitle(@PathVariable String title) {
        return courseService.viewCourseDetails(title);
    }

    @GetMapping("/{id}")
    public Course getById(@PathVariable Long id) {
        return courseService.viewCourseDetailsById(id);
    }

    /*
    * http POST :9001/api/courses title="Microservices with Spring Boot" author="John Doe" price:=29.79 publisher="GitHub"
    * http POST :9001/api/courses title="Spring Boot in Action" author="John Doe" price:=69.45 publisher="GitHub"
    * */
    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public Course post(@Valid @RequestBody Course course) {
        logger.info("Received request to create course: {}", course.getTitle());
        Course savedCourse = courseService.addCourse(course);
        if (savedCourse.getId() == null) {
            logger.error("Course was not saved correctly! ID is null.");
            throw new IllegalStateException("Failed to save course, ID is null!");
        }
        logger.info("Course created successfully with ID: {}", savedCourse.getId());
        return savedCourse;
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void delete(@PathVariable Long id) {
        courseService.removeCourse(id);
    }

    @PutMapping("/{id}")
    public Course put(@PathVariable Long id, @Valid @RequestBody Course course) {
        return courseService.editCourseDetails(id, course);
    }

}


// Node: post
// Node: getTitle
// Node: addCourse
// Node: getId
// Node: error
// Node: IllegalStateException
// Node: editCourseDetails
package io.javatab.microservices.core.course.domain;


import jakarta.persistence.*;
import jakarta.validation.constraints.*;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;

import java.time.Instant;
import java.util.Objects;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

@Entity
@EntityListeners(AuditingEntityListener.class)
public class Course {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @NotBlank(message = "The book title must be defined.")
    private String title;

    @NotBlank(message = "The book author must be defined.")
    private String author;

    @NotNull(message = "The book price must be defined.")
    @Positive(message = "The book price must be greater than zero.")
    private Double price;

    private String publisher;

    @CreatedDate
    private Instant createdDate;

    @LastModifiedDate
    private Instant lastModifiedDate;

    @Version
    private int version;

    public Course() {}

    public Course(Long id, String title, String author, Double price, String publisher, Instant createdDate, Instant lastModifiedDate, int version) {
        this.id = id;
        this.title = title;
        this.author = author;
        this.price = price;
        this.publisher = publisher;
        this.createdDate = createdDate;
        this.lastModifiedDate = lastModifiedDate;
        this.version = version;
    }

    public static Course of(String title, String author, Double price, String publisher) {
        return new Course(null, title, author, price, publisher, null, null, 0);
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public String getAuthor() {
        return author;
    }

    public void setAuthor(String author) {
        this.author = author;
    }

    public Double getPrice() {
        return price;
    }

    public void setPrice(Double price) {
        this.price = price;
    }

    public String getPublisher() {
        return publisher;
    }

    public void setPublisher(String publisher) {
        this.publisher = publisher;
    }

    public Instant getCreatedDate() {
        return createdDate;
    }

    public void setCreatedDate(Instant createdDate) {
        this.createdDate = createdDate;
    }

    public Instant getLastModifiedDate() {
        return lastModifiedDate;
    }

    public void setLastModifiedDate(Instant lastModifiedDate) {
        this.lastModifiedDate = lastModifiedDate;
    }

    public int getVersion() {
        return version;
    }

    public void setVersion(int version) {
        this.version = version;
    }

    @Override
    public boolean equals(Object o) {
        if (o == null || getClass() != o.getClass()) return false;
        Course course = (Course) o;
        return getVersion() == course.getVersion() && Objects.equals(getId(), course.getId()) && Objects.equals(getTitle(), course.getTitle()) && Objects.equals(getAuthor(), course.getAuthor()) && Objects.equals(getPrice(), course.getPrice()) && Objects.equals(getPublisher(), course.getPublisher()) && Objects.equals(getCreatedDate(), course.getCreatedDate()) && Objects.equals(getLastModifiedDate(), course.getLastModifiedDate());
    }

    @Override
    public int hashCode() {
        return Objects.hash(getId(), getTitle(), getAuthor(), getPrice(), getPublisher(), getCreatedDate(), getLastModifiedDate(), getVersion());
    }
}


// Node: setTitle
// Node: getAuthor
// Node: setAuthor
// Node: getPrice
// Node: setPrice
// Node: getPublisher
// Node: setPublisher
// Node: getCreatedDate
// Node: getLastModifiedDate
// Node: getVersion
// Node: equals
// Node: getClass
// Node: hashCode
// Node: hash
package io.javatab.microservices.core.course.domain;

public class CourseAlreadyExitsException extends RuntimeException {
    public CourseAlreadyExitsException(String title) {
        super("A course with title " + title + " already exists.");
    }
}


// Node: repos/cloned_ms_repos/spring-boot-based-microservices/microservices/course-service/src/main/java/io/javatab/microservices/core/course/domain/CourseAlreadyExitsException.java:CourseAlreadyExitsException.<init>
// Node: CourseAlreadyExitsException
package io.javatab.microservices.core.course.domain;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

@Service
public class CourseService {

    private final Logger logger = LoggerFactory.getLogger(CourseService.class);

    private final CourseRepository courseRepository;

    public CourseService(CourseRepository courseRepository) {
        this.courseRepository = courseRepository;
    }

    public Iterable<Course> viewCourses() {
        return courseRepository.findAll();
    }

    public Course viewCourseDetails(String title) {
        return courseRepository.findByTitle(title)
                .orElseThrow(() -> new CourseNotFoundException(title));
    }

    public Course viewCourseDetailsById(Long id) {
        return courseRepository.findById(id)
                .orElseThrow(() -> new CourseNotFoundException(String.valueOf(id)));
    }

    public Course addCourse(Course course) {

        logger.info("Checking if course '{}' already exists...", course.getTitle());

        if (courseRepository.existsByTitle(course.getTitle())) {
            logger.warn("Course '{}' already exists! Throwing exception.", course.getTitle());
            throw new CourseAlreadyExitsException(course.getTitle());
        }

        Course savedCourse = courseRepository.save(course);
        logger.info("Course '{}' saved successfully with ID: {}", savedCourse.getTitle(), savedCourse.getId());

        return savedCourse;
    }

    public void removeCourse(Long id) {
        courseRepository.deleteById(id);
    }

    public Course editCourseDetails(Long id, Course course) {
        return courseRepository.findById(id)
                .map(existingCourse -> {
                    existingCourse.setTitle(course.getTitle());
                    existingCourse.setAuthor(course.getAuthor());
                    existingCourse.setPrice(course.getPrice());
                    existingCourse.setPublisher(course.getPublisher());
                    return courseRepository.save(existingCourse);
                }).orElseGet(() -> addCourse(course));

    }
}


// Node: warn
// Node: save
// Node: orElseGet
package io.javatab.microservices.composite.course;

import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;
import jakarta.annotation.PostConstruct;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;


import java.util.Random;


/*
* Just for manual test for metrics and errors which doesn't sit under security
* */
@RestController
@RequestMapping("/api/metrics")
public class MetricsController {
    private final Logger logger = LoggerFactory.getLogger(MetricsController.class);
    private final MeterRegistry meterRegistry;
    private Counter requestCounter;
    private Timer requestTimer;

    public MetricsController(MeterRegistry meterRegistry) {
        this.meterRegistry = meterRegistry;
    }

    @PostConstruct
    public void init() {
        // Initialize custom metrics
        requestCounter = Counter
                .builder("api.requests.total")
                .description("Total number of API requests")
                .tags("endpoint", "/hello")
                .register(meterRegistry);

        requestTimer = Timer
                .builder("api.request.duration")
                .description("Time taken to process requests")
                .tags("endpoint", "/hello")
                .register(meterRegistry);
    }

    @GetMapping("/hello")
    public String hello() {
        logger.info("Hello endpoint called");
        logger.warn("This is a warning log");
        // Record request count
        requestCounter.increment();

        // Record execution time
        return requestTimer.record(() -> {
            try {
                // Simulate some work
                int sleepTime = new Random().nextInt(1000);
                Thread.sleep(sleepTime);
                return "Hello, World!";
            } catch (InterruptedException e) {
                return "Error occurred";
            }
        });
    }

    @GetMapping("/runtime-error")
    public String error() {
        logger.error("An error occurred", new RuntimeException("Test exception"));
        return "Error logged";
    }

    @GetMapping("/error")
    public String triggerError() {
        throw new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, "Something went wrong!");
    }
}

// Node: RuntimeException
