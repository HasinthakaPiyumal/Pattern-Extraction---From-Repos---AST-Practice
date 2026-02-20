// Cluster 5

package net.javaguides.order_service.entity;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

@Getter
@RequiredArgsConstructor
public enum OrderStatus {
    PENDING("Pending"),
    PROCESSING("Processing"),
    SHIPPING("Shipping"),
    DELIVERED("Delivered"),
    CANCELED("Canceled");

    public final String label;
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/order-service/src/main/java/net/javaguides/order_service/entity/OrderStatus.java:OrderStatus.<init>
// Node: PENDING
// Node: PROCESSING
// Node: SHIPPING
// Node: DELIVERED
// Node: CANCELED
package net.javaguides.payment_service.entity;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

@Getter
@RequiredArgsConstructor
public enum PaymentStatus {
    PENDING("Pending"),
    SUCCESS("Success"),
    FAILED("Failed"),
    REFUND("Refund");

    public final String label;
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/payment-service/src/main/java/net/javaguides/payment_service/entity/PaymentStatus.java:PaymentStatus.<init>
// Node: SUCCESS
// Node: FAILED
// Node: REFUND
