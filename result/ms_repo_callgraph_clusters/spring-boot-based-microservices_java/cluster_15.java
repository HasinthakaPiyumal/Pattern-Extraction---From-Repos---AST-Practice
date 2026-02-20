// Cluster 15

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


// Node: repos/cloned_ms_repos/spring-boot-based-microservices/microservices/course-service/src/main/java/io/javatab/microservices/core/course/domain/Course.java:Course.<init>
// Node: EntityListeners
// Node: GeneratedValue
// Node: NotBlank
// Node: NotNull
// Node: Positive
// Node: Course
// Node: of
package io.javatab.microservices.core.review.web;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class ReviewDTO {

    @NotNull(message = "The course id must be defined.")
    private int courseId;
    @NotBlank(message = "Author is required")
    @Size(min = 4, max = 40, message = "Author must be between 4 and 40 characters")
    private String author;
    @NotBlank(message = "Content is required")
    @Size(min = 5, max = 500, message = "Content must be between 50 and 500 characters")
    private String content;
    @NotBlank(message = "Email is required")
    @Email(message = "Email should be valid")
    private String email;

}


// Node: repos/cloned_ms_repos/spring-boot-based-microservices/microservices/review-service/src/main/java/io/javatab/microservices/core/review/web/ReviewDTO.java:ReviewDTO.<init>
// Node: Size
// Node: Email
