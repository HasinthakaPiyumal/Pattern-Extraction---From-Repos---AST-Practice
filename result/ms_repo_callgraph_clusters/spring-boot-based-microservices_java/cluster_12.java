// Cluster 12

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


// Node: getByTitle
// Node: viewCourseDetails
// Node: getById
// Node: viewCourseDetailsById
// Node: delete
// Node: removeCourse
// Node: PutMapping
package io.javatab.microservices.core.course.domain;

import jakarta.transaction.Transactional;
import org.springframework.data.repository.CrudRepository;

import java.util.Optional;

public interface CourseRepository extends CrudRepository<Course,Long> {

    Optional<Course> findByTitle(String title);
    Optional<Course> findById(Long id);
    boolean existsByTitle(String title);


    @Transactional
    void deleteById(Long id);

}


// Node: repos/cloned_ms_repos/spring-boot-based-microservices/microservices/course-service/src/main/java/io/javatab/microservices/core/course/domain/CourseRepository.java:CourseRepository.<init>
// Node: findByTitle
// Node: findById
// Node: existsByTitle
// Node: deleteById
package io.javatab.microservices.core.course.domain;

public class CourseNotFoundException extends RuntimeException {
    public CourseNotFoundException(String title) {
        super("The course with title " + title + " was not found.");
    }
}


// Node: repos/cloned_ms_repos/spring-boot-based-microservices/microservices/course-service/src/main/java/io/javatab/microservices/core/course/domain/CourseNotFoundException.java:CourseNotFoundException.<init>
// Node: CourseNotFoundException
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


// Node: orElseThrow
// Node: valueOf
// Node: getReviewId
package io.javatab.microservices.core.review.domain;

import io.javatab.microservices.core.review.web.ReviewDTO;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class ReviewService {

    private static final Logger logger = LoggerFactory.getLogger(ReviewService.class);
    private final ReviewRepository reviewRepository;

    public ReviewService(ReviewRepository reviewRepository) {
        this.reviewRepository = reviewRepository;
    }

    @Transactional
    public Review addReview(ReviewDTO reviewDto) {
        logger.info("Adding new review with email: {}", reviewDto.getEmail());
        Review aReview = Review.builder()
                .courseId(reviewDto.getCourseId())
                .author(reviewDto.getAuthor())
                .content(reviewDto.getContent())
                .email(reviewDto.getEmail())
                .build();
        return reviewRepository.save(aReview);
    }

    @Transactional(readOnly = true)
    public List<Review> getAllReviews() {
        logger.info("Fetching all reviews");
        return reviewRepository.findAll();
    }

    @Transactional(readOnly = true)
    public List<Review> getReviewsByEmail(String email) {
        logger.info("Fetching review with email: {}", email);
        return reviewRepository.findByEmail(email);
    }

    @Transactional(readOnly = true)
    public List<Review> getReviewsByCourseIdAndEmail(Long courseId, String email) {
        logger.info("Fetching review with course Id: {} and by email {}", courseId, email);
        return reviewRepository.findByCourseIdAndEmail(courseId, email);
    }

    @Transactional(readOnly = true)
    public List<Review> getReviewsByCourseId(Long courseId) {
        logger.info("Fetching review with course Id : {}", courseId);
        return reviewRepository.findByCourseId(courseId);
    }

    @Transactional
    public void deleteReview(String id) {
        logger.info("Deleting review with id: {}", id);
        if (!reviewRepository.existsById(id)) {
            throw new ReviewNotFoundException("Review not found with id: " + id);
        }
        reviewRepository.deleteById(id);
    }

    @Transactional
    public Review getReviewId(String id) {
        logger.info("Fetching review with id: {}", id);
        return reviewRepository.findById(id)
                .orElseThrow(() -> new ReviewNotFoundException(id));
    }
}


