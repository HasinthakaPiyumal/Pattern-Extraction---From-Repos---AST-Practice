// Cluster 69

package net.chrisrichardson.ftgo.restaurantservice.aws;

import com.amazonaws.services.lambda.runtime.events.APIGatewayProxyResponseEvent;
import io.eventuate.common.json.mapper.JSonMapper;

import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

public class ApiGatewayResponse {
  private final int statusCode;
  private final String body;
  private final Map<String, String> headers;
  private final boolean isBase64Encoded;

  public ApiGatewayResponse(int statusCode, String body, Map<String, String> headers, boolean isBase64Encoded) {
    this.statusCode = statusCode;
    this.body = body;
    this.headers = headers;
    this.isBase64Encoded = isBase64Encoded;
  }

  public int getStatusCode() {
    return statusCode;
  }

  public String getBody() {
    return body;
  }

  public Map<String, String> getHeaders() {
    return headers;
  }

  // API Gateway expects the property to be called "isBase64Encoded" => isIs
  public boolean isIsBase64Encoded() {
    return isBase64Encoded;
  }

  public static Builder builder() {
    return new Builder();
  }

  public static class Builder {
    private int statusCode = 200;
    private Map<String, String> headers = Collections.emptyMap();
    private String rawBody;
    private Object objectBody;
    private byte[] binaryBody;
    private boolean base64Encoded;

    public Builder setStatusCode(int statusCode) {
      this.statusCode = statusCode;
      return this;
    }

    public Builder setHeaders(Map<String, String> headers) {
      this.headers = headers;
      return this;
    }

    public Builder setRawBody(String rawBody) {
      this.rawBody = rawBody;
      return this;
    }

    public Builder setObjectBody(Object objectBody) {
      this.objectBody = objectBody;
      return this;
    }

    public Builder setBinaryBody(byte[] binaryBody) {
      this.binaryBody = binaryBody;
      setBase64Encoded(true);
      return this;
    }

    public Builder setBase64Encoded(boolean base64Encoded) {
      this.base64Encoded = base64Encoded;
      return this;
    }

    public APIGatewayProxyResponseEvent build() {
      String body = null;
      if (rawBody != null) {
        body = rawBody;
      } else if (objectBody != null) {
        body = JSonMapper.toJson(objectBody);
      } else if (binaryBody != null) {
        body = new String(Base64.getEncoder().encode(binaryBody), StandardCharsets.UTF_8);
      }
      APIGatewayProxyResponseEvent response = new APIGatewayProxyResponseEvent();
      response.setStatusCode(statusCode);
      response.setBody(body);
      response.setHeaders(headers);
      return response;
    }
  }

  public static APIGatewayProxyResponseEvent buildErrorResponse(AwsLambdaError error) {
    return ApiGatewayResponse.builder()
            .setStatusCode(Integer.valueOf(error.getCode()))
            .setObjectBody(error)
            .setHeaders(applicationJsonHeaders())
            .build();
  }

  public static Map<String, String> applicationJsonHeaders() {
    Map<String, String> headers = new HashMap<>();
    headers.put("Content-Type", "application/json");
    return headers;
  }
}

// Node: setBinaryBody
// Node: setBase64Encoded
package net.chrisrichardson.ftgo.restaurantservice.aws;

import org.apache.commons.lang.builder.ToStringBuilder;

import java.util.Map;
import java.util.Optional;

public class ApiGatewayRequest {

  private String resource;
  private String path;
  private String httpMethod;
  private Map<String, String> headers;
  private Map<String, String> queryStringParameters;
  private Map<String, String> pathParameters;
  private Map<String, String> stageVariables;
  private RequestContext requestContext;
  private String body;
  private boolean isBase64Encoded;

  public String getResource() {
    return resource;
  }

  public void setResource(String resource) {
    this.resource = resource;
  }

  public String getPath() {
    return path;
  }

  public void setPath(String path) {
    this.path = path;
  }

  public String getHttpMethod() {
    return httpMethod;
  }

  public void setHttpMethod(String httpMethod) {
    this.httpMethod = httpMethod;
  }

  public Map<String, String> getHeaders() {
    return headers;
  }

  public void setHeaders(Map<String, String> headers) {
    this.headers = headers;
  }

  public Map<String, String> getQueryStringParameters() {
    return queryStringParameters;
  }

  public void setQueryStringParameters(Map<String, String> queryStringParameters) {
    this.queryStringParameters = queryStringParameters;
  }

  public Map<String, String> getPathParameters() {
    return pathParameters;
  }

  public void setPathParameters(Map<String, String> pathParameters) {
    this.pathParameters = pathParameters;
  }

  public Map<String, String> getStageVariables() {
    return stageVariables;
  }

  public void setStageVariables(Map<String, String> stageVariables) {
    this.stageVariables = stageVariables;
  }

  public RequestContext getRequestContext() {
    return requestContext;
  }

  public void setRequestContext(RequestContext requestContext) {
    this.requestContext = requestContext;
  }

  public String getBody() {
    return body;
  }

  public void setBody(String body) {
    this.body = body;
  }

  public boolean isBase64Encoded() {
    return isBase64Encoded;
  }

  public void setBase64Encoded(boolean base64Encoded) {
    isBase64Encoded = base64Encoded;
  }

  @Override
  public String toString() {
    return ToStringBuilder.reflectionToString(this);
  }

  public String getPathParam(String paramName) {
    return Optional.ofNullable(this.getPathParameters())
            .map(paramsMap -> paramsMap.get(paramName))
            .orElse(null);
  }
}

