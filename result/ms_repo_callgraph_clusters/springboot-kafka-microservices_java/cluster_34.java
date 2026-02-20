// Cluster 34

package net.javaguides.identity_service.entity.converter;

import jakarta.persistence.AttributeConverter;
import jakarta.persistence.Converter;
import net.javaguides.identity_service.enums.ERole;

@Converter(autoApply = true)
public class RoleConverter implements AttributeConverter<ERole, String> {

    @Override
    public String convertToDatabaseColumn(ERole status) {
        if(status == null){
            return null;
        }
        return status.getLabel();
    }

    @Override
    public ERole convertToEntityAttribute(String label) {
        if(label == null){
            return null;
        }
        return switch(label) {
            case "Administrator" -> ERole.ADMINISTRATOR;
            case "Employee" -> ERole.EMPLOYEE;
            case "Customer" -> ERole.CUSTOMER;
            default -> throw new IllegalArgumentException("Unknown role: " + label);
        };
    }
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/identity-service/src/main/java/net/javaguides/identity_service/entity/converter/RoleConverter.java:RoleConverter.<init>
// Node: Converter
package net.javaguides.payment_service.entity.converter;

import jakarta.persistence.AttributeConverter;
import jakarta.persistence.Converter;
import net.javaguides.payment_service.entity.PaymentStatus;

@Converter(autoApply = true)
public class PaymentStatusConverter implements AttributeConverter<PaymentStatus, String> {

    @Override
    public String convertToDatabaseColumn(PaymentStatus status) {
        if(status == null){
            return null;
        }
        return status.getLabel();
    }

    @Override
    public PaymentStatus convertToEntityAttribute(String label) {
        if(label == null){
            return null;
        }
        return switch(label) {
            case "Pending" -> PaymentStatus.PENDING;
            case "Success" -> PaymentStatus.SUCCESS;
            case "Failed" -> PaymentStatus.FAILED;
            default -> throw new IllegalArgumentException("Unknown payment status: " + label);
        };
    }
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/payment-service/src/main/java/net/javaguides/payment_service/entity/converter/PaymentStatusConverter.java:PaymentStatusConverter.<init>
