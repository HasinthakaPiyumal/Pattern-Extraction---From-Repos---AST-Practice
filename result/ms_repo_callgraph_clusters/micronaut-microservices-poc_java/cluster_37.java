// Cluster 37

// Node: covers
package pl.altkom.asc.lab.micronaut.poc.policy.domain;

import com.fasterxml.jackson.annotation.JsonIgnore;
import java.math.BigDecimal;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.vo.DateRange;

import javax.persistence.*;
import java.time.LocalDate;
import java.util.Set;

@Entity
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
@Getter
public class PolicyVersion {
    @Id
    @GeneratedValue
    private Long id;

    @JsonIgnore
    @ManyToOne
    @JoinColumn(name = "POLICY_ID")
    private Policy policy;

    private Long versionNumber;

    private String productCode;

    private Person policyHolder;

    private String accountNumber;

    @Embedded
    @AttributeOverrides({
            @AttributeOverride(name = "from", column = @Column(name = "cover_from")),
            @AttributeOverride(name = "to", column = @Column(name = "cover_to"))
    })
    private DateRange coverPeriod;

    @Embedded
    @AttributeOverrides({
            @AttributeOverride(name = "from", column = @Column(name = "version_from")),
            @AttributeOverride(name = "to", column = @Column(name = "version_to"))
    })
    private DateRange versionValidityPeriod;

    @OneToMany(mappedBy = "policyVersion", cascade = CascadeType.ALL)
    private Set<Cover> covers;
    
    private BigDecimal totalPremiumAmount;

    CoverCollection covers() {
        return new CoverCollection(this, covers);
    }
}


// Node: CoverCollection
package pl.altkom.asc.lab.micronaut.poc.product.service.infrastructure.adapters.web;

import lombok.AccessLevel;
import lombok.NoArgsConstructor;
import pl.altkom.asc.lab.micronaut.poc.product.service.api.v1.CoverDto;
import pl.altkom.asc.lab.micronaut.poc.product.service.api.v1.ProductDto;
import pl.altkom.asc.lab.micronaut.poc.product.service.api.v1.questions.*;
import pl.altkom.asc.lab.micronaut.poc.product.service.domain.*;

import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

@NoArgsConstructor(access = AccessLevel.PRIVATE)
final class ProductsAssembler {

    static List<ProductDto> map(List<Product> products) {
        return products.stream()
                .map(ProductsAssembler::map)
                .collect(Collectors.toList());
    }

    static ProductDto map(Product product) {
        return ProductDto.builder()
                .code(product.getCode())
                .name(product.getName())
                .image(product.getImage())
                .description(product.getDescription())
                .covers(mapCovers(product))
                .questions(mapQuestions(product))
                .maxNumberOfInsured(product.getMaxNumberOfInsured())
                .icon(product.getIcon())
                .build();
    }

    private static List<QuestionDto> mapQuestions(Product product) {
        return product.getQuestions().stream()
                .map(ProductsAssembler::mapQuestion)
                .collect(Collectors.toList());
    }

    private static List<CoverDto> mapCovers(Product product) {
        return product.getCovers().stream()
                .map(ProductsAssembler::mapCover)
                .collect(Collectors.toList());
    }

    private static CoverDto mapCover(Cover cover) {
        return new CoverDto(
                cover.getCode(),
                cover.getName(),
                cover.getDescription(),
                cover.isOptional(),
                cover.getSumInsured()
        );
    }

    private static QuestionDto mapQuestion(Question question) {
        QuestionDto dto = mapToNumericIfFit(question);

        dto = dto == null ? mapToDateIfFit(question) : dto;
        dto = dto == null ? mapToChoiceIfFit(question) : dto;

        return dto;
    }

    private static QuestionDto mapToChoiceIfFit(Question question) {
        if (!(question instanceof ChoiceQuestion))
            return null;

        return new ChoiceQuestionDto(question.getCode(), question.getIndex(), question.getText(), mapChoices(question));
    }

    private static List<ChoiceDto> mapChoices(Question question) {
        List<Choice> choices = ((ChoiceQuestion) question).getChoices();

        if (choices == null)
            return new ArrayList<>();

        return choices.stream()
                .map(x -> new ChoiceDto(x.getCode(), x.getLabel()))
                .collect(Collectors.toList());
    }

    private static QuestionDto mapToDateIfFit(Question question) {
        if (!(question instanceof DateQuestion))
            return null;

        return new DateQuestionDto(question.getCode(), question.getIndex(), question.getText());
    }

    private static QuestionDto mapToNumericIfFit(Question question) {
        if (!(question instanceof NumericQuestion))
            return null;

        return new NumericQuestionDto(question.getCode(), question.getIndex(), question.getText());
    }

}


// Node: code
// Node: name
// Node: getName
// Node: image
// Node: getImage
// Node: description
// Node: getDescription
// Node: mapCovers
// Node: questions
// Node: mapQuestions
// Node: maxNumberOfInsured
// Node: getMaxNumberOfInsured
// Node: icon
// Node: getIcon
// Node: mapCover
// Node: CoverDto
// Node: isOptional
// Node: getSumInsured
package pl.altkom.asc.lab.micronaut.poc.gateway;


import io.micronaut.http.annotation.Controller;
import io.micronaut.http.annotation.Get;
import io.micronaut.http.annotation.Post;
import io.micronaut.http.annotation.QueryValue;
import io.micronaut.security.annotation.Secured;
import io.micronaut.security.rules.SecurityRule;
import io.reactivex.Maybe;
import pl.altkom.asc.lab.micronaut.poc.gateway.client.v1.PolicyGatewayClient;
import pl.altkom.asc.lab.micronaut.poc.gateway.client.v1.PolicySearchGatewayClient;
import pl.altkom.asc.lab.micronaut.poc.policy.search.service.api.v1.queries.findpolicy.FindPolicyQueryResult;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createpolicy.CreatePolicyCommand;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createpolicy.CreatePolicyResult;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.terminatepolicy.TerminatePolicyCommand;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.terminatepolicy.TerminatePolicyResult;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.queries.getpolicydetails.GetPolicyDetailsQueryResult;

import javax.inject.Inject;
import java.security.Principal;

@Secured(SecurityRule.IS_AUTHENTICATED)
@Controller("/api/policies")
public class PolicyGatewayController {

    @Inject
    private PolicyGatewayClient policyClient;
    @Inject
    private PolicySearchGatewayClient policySearchClient;

    @Get
    Maybe<FindPolicyQueryResult> policies(@QueryValue(value = "q", defaultValue = "*") String q) {
        return policySearchClient.policies(q);
    }

    @Get("/{policyNumber}")
    GetPolicyDetailsQueryResult get(String policyNumber) {
        return policyClient.get(policyNumber);
    }

    @Post("/create")
    CreatePolicyResult create(CreatePolicyCommand cmd, Principal principal) {
        cmd.setAgentLogin(principal.getName());
        return policyClient.create(cmd);
    }

    @Post("/terminate")
    TerminatePolicyResult terminate(TerminatePolicyCommand cmd) {
        return policyClient.terminate(cmd);
    }

}


// Node: setAgentLogin
