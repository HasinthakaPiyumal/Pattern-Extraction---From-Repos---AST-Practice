// Cluster 9

package io.javatab.microservices.core.course.web;

import io.javatab.microservices.core.course.domain.CourseAlreadyExitsException;
import io.javatab.microservices.core.course.domain.CourseNotFoundException;
import org.springframework.http.HttpStatus;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.HashMap;
import java.util.Map;

@RestControllerAdvice
public class CourseControllerAdvice {

    @ExceptionHandler(CourseNotFoundException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    String courseNotFoundHandler(CourseNotFoundException ex) {
        return ex.getMessage();
    }

    @ExceptionHandler(CourseAlreadyExitsException.class)
    @ResponseStatus(HttpStatus.UNPROCESSABLE_ENTITY)
    String courseAlreadyExistsHandler(CourseAlreadyExitsException ex) {
        return ex.getMessage();
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public Map<String, String> handleValidationExceptions(MethodArgumentNotValidException ex) {
        Map<String, String> errorsMap = new HashMap<>();
        ex.getBindingResult().getAllErrors().forEach(error -> {
            String fieldName = ((FieldError) error).getField();
            String errorMessage = error.getDefaultMessage();
            errorsMap.put(fieldName, errorMessage);
        });
        return errorsMap;
    }

}

// Node: repos/cloned_ms_repos/spring-boot-based-microservices/microservices/course-service/src/main/java/io/javatab/microservices/core/course/web/CourseControllerAdvice.java:CourseControllerAdvice.<init>
// Node: ExceptionHandler
// Node: ResponseStatus
// Node: courseNotFoundHandler
// Node: getMessage
// Node: courseAlreadyExistsHandler
// Node: handleValidationExceptions
// Node: getBindingResult
// Node: getAllErrors
// Node: getField
// Node: getDefaultMessage
/*
package io.javatab.microservices.core.review.web;

import io.javatab.microservices.core.review.domain.ReviewNotFoundException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;

import java.util.stream.Collectors;

@ControllerAdvice
public class ReviewControllerAdvice {
    @ExceptionHandler(ReviewNotFoundException.class)
    public ResponseEntity<String> handleNotFound(ReviewNotFoundException ex) {
        return new ResponseEntity<>(ex.getMessage(), HttpStatus.NOT_FOUND);
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<String> handleValidationExceptions(MethodArgumentNotValidException ex) {
        String errorMessage = ex.getBindingResult()
                .getFieldErrors()
                .stream()
                .map(error -> error.getField() + ": " + error.getDefaultMessage())
                .collect(Collectors.joining(", "));
        return new ResponseEntity<>(errorMessage, HttpStatus.BAD_REQUEST);
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<String> handleGenericException(Exception ex) {
        return new ResponseEntity<>("An unexpected error occurred", HttpStatus.INTERNAL_SERVER_ERROR);
    }
}
*/


// Node: repos/cloned_ms_repos/spring-boot-based-microservices/microservices/review-service/src/main/java/io/javatab/microservices/core/review/web/ReviewControllerAdvice.java:ReviewControllerAdvice.<init>
// Node: handleNotFound
// Node: getFieldErrors
// Node: collect
// Node: joining
