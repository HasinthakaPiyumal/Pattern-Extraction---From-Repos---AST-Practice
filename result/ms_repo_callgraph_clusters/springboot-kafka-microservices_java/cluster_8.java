// Cluster 8

package net.javaguides.product_service.repository;

import net.javaguides.product_service.entity.AttributeValue;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface AttributeValueRepository extends JpaRepository<AttributeValue, Long> {
    List<AttributeValue> findByProductVariantId(Long productVariantId);
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/product-service/src/main/java/net/javaguides/product_service/repository/AttributeValueRepository.java:AttributeValueRepository.<init>
// Node: findByProductVariantId
