// Cluster 12

package net.javaguides.common_lib.entity;

import jakarta.persistence.*;
import lombok.*;

import java.util.Date;

@MappedSuperclass
@Getter
@Setter
@NoArgsConstructor
public abstract class AbstractEntity {

    @Temporal(TemporalType.TIMESTAMP)
    protected Date createdAt;

    @Temporal(TemporalType.TIMESTAMP)
    protected Date updatedAt;

    @Version
    protected int version;

    @PrePersist
    protected void onCreate() {
        createdAt = new Date();
        updatedAt = new Date();
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = new Date();
    }
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/common-lib/src/main/java/net/javaguides/common_lib/entity/AbstractEntity.java:AbstractEntity.<init>
// Node: Temporal
