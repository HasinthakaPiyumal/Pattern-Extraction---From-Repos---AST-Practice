// Cluster 5

package pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createoffer.dto;

import com.fasterxml.jackson.annotation.JsonSubTypes;
import com.fasterxml.jackson.annotation.JsonTypeInfo;

import io.micronaut.core.annotation.Introspected;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Introspected
@NoArgsConstructor
@AllArgsConstructor
@Getter
@Setter
@JsonTypeInfo(
    use = JsonTypeInfo.Id.NAME,
    include = JsonTypeInfo.As.PROPERTY, 
    property = "type")
@JsonSubTypes({
    @JsonSubTypes.Type(value = ChoiceQuestionAnswer.class, name = "choice"),
    @JsonSubTypes.Type(value = TextQuestionAnswer.class, name = "text"),
    @JsonSubTypes.Type(value = NumericQuestionAnswer.class, name = "numeric"),
})
public abstract class QuestionAnswer<T> {
    private String questionCode;
    private T answer;
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-service-api/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/service/api/v1/commands/createoffer/dto/QuestionAnswer.java:QuestionAnswer.<init>
// Node: JsonTypeInfo
// Node: JsonSubTypes
// Node: Type
package pl.altkom.asc.lab.micronaut.poc.product.service.api.v1.questions;

import com.fasterxml.jackson.annotation.JsonSubTypes;
import com.fasterxml.jackson.annotation.JsonTypeInfo;

import io.micronaut.core.annotation.Introspected;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Introspected
@NoArgsConstructor
@Getter
@JsonTypeInfo(
        use = JsonTypeInfo.Id.NAME,
        include = JsonTypeInfo.As.PROPERTY,
        property = "type")
@JsonSubTypes({
        @JsonSubTypes.Type(value = ChoiceQuestionDto.class, name = "choice"),
        @JsonSubTypes.Type(value = DateQuestionDto.class, name = "date"),
        @JsonSubTypes.Type(value = NumericQuestionDto.class, name = "numeric")
})
public class QuestionDto {
    private String code;
    private int index;
    private String text;

    public QuestionDto(String code, int index, String text) {
        this.code = code;
        this.index = index;
        this.text = text;
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/product-service-api/src/main/java/pl/altkom/asc/lab/micronaut/poc/product/service/api/v1/questions/QuestionDto.java:QuestionDto.<init>
// Node: QuestionDto
