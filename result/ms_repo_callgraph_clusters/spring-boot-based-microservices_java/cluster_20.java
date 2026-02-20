// Cluster 20

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

// Node: init
// Node: builder
// Node: description
// Node: tags
// Node: register
package io.javatab.microservices.composite.course.config;

import io.micrometer.core.instrument.Gauge;
import io.micrometer.core.instrument.MeterRegistry;
import jakarta.annotation.PostConstruct;
import org.springframework.context.annotation.Configuration;

import java.util.concurrent.atomic.AtomicInteger;

@Configuration
public class MetricsConfig {

    private final MeterRegistry meterRegistry;
    private final AtomicInteger activeUsers = new AtomicInteger(0);

    public MetricsConfig(MeterRegistry meterRegistry) {
        this.meterRegistry = meterRegistry;
    }

    @PostConstruct
    public void init() {
        // Register a gauge for active users
        Gauge.builder("application.active.users", activeUsers::get)
                .description("Number of active users")
                .register(meterRegistry);
    }

    // Method to update active users (could be called from your service layer)
    public void updateActiveUsers(int count) {
        activeUsers.set(count);
    }
}

// Node: users
package io.javatab.microservices.core.review.web;

import io.javatab.microservices.core.review.domain.Review;
import io.javatab.microservices.core.review.domain.ReviewService;

import jakarta.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController()
@RequestMapping("/api/reviews")
public class ReviewController {

    private static final Logger logger = LoggerFactory.getLogger(ReviewController.class);
    private final ReviewService reviewService;

    public ReviewController(ReviewService reviewService) {
        this.reviewService = reviewService;
    }


    /*
    * http POST :9002/api/reviews courseId:=1 author="John Doe" content="Amazing book"  email="abc@xyz.com"
    * */
    @PostMapping
    public ResponseEntity<Review> addReview(@Valid @RequestBody ReviewDTO review) {
        logger.info("Received request to add review to course id {} by email: {} and ", review.getCourseId(), review.getEmail());
        Review addedReview = reviewService.addReview(review);
        return new ResponseEntity<>(addedReview, HttpStatus.CREATED);
    }

    @GetMapping
    public ResponseEntity<List<Review>> getAllReviews() {
        logger.info("Received request to fetch all reviews");
        return ResponseEntity.ok(reviewService.getAllReviews());
    }

    @GetMapping("/{id}")
    public ResponseEntity<Review> getReviewById(@PathVariable String id) {
        logger.info("Received request to fetch review with id: {}", id);
        return ResponseEntity.ok(reviewService.getReviewId(id));
    }

    @GetMapping(params = {"course"})
    public ResponseEntity<List<Review>> getReviewByCourseId(@RequestParam("course") Long courseId) {
        logger.info("Received request to fetch review with course id: {}", courseId);
        return ResponseEntity.ok(reviewService.getReviewsByCourseId(courseId));
    }

    /*
    * http :9002/api/reviews courseId==1 email==abc@xyz.com
    * or
    * http GET "http://localhost:9002/api/reviews?courseId=1&email=abc@xyz.com"
     * */
    @GetMapping(params = {"courseId", "email"})
    public ResponseEntity<List<Review>> getReviewByCourseIdAndEmail(@RequestParam("courseId") Long courseId, @RequestParam("email") String email) {
        logger.info("Received request to fetch review with course id: {} and email : {}", courseId, email);
        return ResponseEntity.ok(reviewService.getReviewsByCourseIdAndEmail(courseId, email));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteReview(@PathVariable String id) {
        logger.info("Received request to delete review with id: {}", id);
        reviewService.deleteReview(id);
        return ResponseEntity.noContent().build();
    }
}


// Node: addReview
// Node: getCourseId
// Node: getEmail
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


// Node: courseId
// Node: author
// Node: content
// Node: getContent
// Node: email
