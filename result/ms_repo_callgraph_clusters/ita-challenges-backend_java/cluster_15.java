// Cluster 15

package com.itachallenge.document.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.itachallenge.document.service.DocumentService;
import io.swagger.v3.core.util.Json;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.Map;

@Configuration
public class OpenApiConfig {
    private final DocumentService documentService;

    public OpenApiConfig(DocumentService documentService) {
        this.documentService = documentService;
    }

    public static OpenAPI parseOpenApiSpec(String spec) {

        ObjectMapper objectMapper = Json.mapper();
        try {
            return objectMapper.readValue(spec, OpenAPI.class);
        } catch (Exception e) {
            throw new RuntimeException("Error parsing OpenAPI spec: " + e.getMessage());
        }
    }

    @Bean
    public OpenAPI allOpenAPI() {

        String jsonApiSpecChallenge = documentService.getSwaggerChallengeDocsStr();
        String jsonApiSpecUser = documentService.getSwaggerUserDocsStr();
        String jsonApiSpecAuth = documentService.getSwaggerAuthDocsStr();

        OpenAPI challengeApi = parseOpenApiSpec(jsonApiSpecChallenge);
        OpenAPI userApi = parseOpenApiSpec(jsonApiSpecUser);
        OpenAPI authApi = parseOpenApiSpec(jsonApiSpecAuth);

        OpenAPI allApi = new OpenAPI();

        allApi.setInfo(new Info()
                .title("ITA Challenges APIs Documentation")
                .version("1.0")
                .description("Centralized documentation for ITA Challenges APIs. Explore and understand the available services for authentication, challenges, user management, scoring, and more.")
        );
        allApi.setExtensions(Map.of(
                "itachallenge-challenge-api", challengeApi,
                "itachallenge-user-api", userApi,
                "itachallenge-auth-api", authApi
        ));

        return allApi;
    }
}



// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-document/src/main/java/com/itachallenge/document/config/OpenApiConfig.java:OpenApiConfig.<init>
// Node: OpenApiConfig
package com.itachallenge.document.controller;

import com.itachallenge.document.config.OpenApiConfig;
import com.itachallenge.document.service.DocumentService;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;

@TestConfiguration
public class TestConfig {
    private DocumentService documentService;

    @Bean
    public OpenApiConfig openApiConfig() {
        return new OpenApiConfig(documentService);
    }
}


// Node: openApiConfig
