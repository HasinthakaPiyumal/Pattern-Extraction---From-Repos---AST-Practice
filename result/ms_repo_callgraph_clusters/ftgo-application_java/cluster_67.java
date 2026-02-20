// Cluster 67

// Node: setId
package net.chrisrichardson.ftgo.restaurantservice.web;

import net.chrisrichardson.ftgo.restaurantservice.domain.Restaurant;
import net.chrisrichardson.ftgo.restaurantservice.domain.RestaurantService;
import net.chrisrichardson.ftgo.restaurantservice.domain.CreateRestaurantRequest;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping(path = "/restaurants")
public class RestaurantController {

  @Autowired
  private RestaurantService restaurantService;

  @RequestMapping(method = RequestMethod.POST)
  public CreateRestaurantResponse create(@RequestBody CreateRestaurantRequest request) {
    Restaurant r = restaurantService.create(request);
    return new CreateRestaurantResponse(r.getId());
  }

  @RequestMapping(method = RequestMethod.GET, path = "/{restaurantId}")
  public ResponseEntity<GetRestaurantResponse> get(@PathVariable long restaurantId) {
    return restaurantService.findById(restaurantId)
            .map(r -> new ResponseEntity<>(makeGetRestaurantResponse(r), HttpStatus.OK))
            .orElseGet(() -> new ResponseEntity<>(HttpStatus.NOT_FOUND));
  }

  private GetRestaurantResponse makeGetRestaurantResponse(Restaurant r) {
    return new GetRestaurantResponse(r.getId(), r.getName());
  }


}


// Node: CreateRestaurantResponse
package net.chrisrichardson.ftgo.restaurantservice.web;

public class GetRestaurantResponse {
  private Long id;

  public Long getId() {
    return id;
  }

  public void setId(Long id) {
    this.id = id;
  }

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  private String name;

  public GetRestaurantResponse() {
  }

  public GetRestaurantResponse(Long id, String name) {
    this.id = id;
    this.name = name;
  }
}


package net.chrisrichardson.ftgo.restaurantservice.web;

public class CreateRestaurantResponse {
  private long id;

  public CreateRestaurantResponse() {
  }

  public long getId() {
    return id;
  }

  public void setId(long id) {
    this.id = id;
  }

  public CreateRestaurantResponse(long id) {
    this.id = id;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-restaurant-service/src/main/java/net/chrisrichardson/ftgo/restaurantservice/web/CreateRestaurantResponse.java:CreateRestaurantResponse.<init>
package net.chrisrichardson.ftgo.restaurantservice.domain;

import javax.persistence.Access;
import javax.persistence.AccessType;
import javax.persistence.Embedded;
import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.Id;
import javax.persistence.Table;

@Entity
@Table(name = "restaurants")
@Access(AccessType.FIELD)
public class Restaurant {

  @Id
  @GeneratedValue
  private Long id;

  private String name;

  @Embedded
  private RestaurantMenu menu;

  private Restaurant() {
  }

  public void setId(Long id) {
    this.id = id;
  }

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }


  public Restaurant(String name, RestaurantMenu menu) {
    this.name = name;
    this.menu = menu;
  }


  public Long getId() {
    return id;
  }

  public RestaurantMenu getMenu() {
    return menu;
  }
}


package net.chrisrichardson.ftgo.restaurantservice.domain;

import net.chrisrichardson.ftgo.common.Money;
import org.apache.commons.lang.builder.EqualsBuilder;
import org.apache.commons.lang.builder.HashCodeBuilder;
import org.apache.commons.lang.builder.ToStringBuilder;

import javax.persistence.Access;
import javax.persistence.AccessType;
import javax.persistence.Embeddable;

@Embeddable
@Access(AccessType.FIELD)
public class MenuItem {

  private String id;
  private String name;
  private Money price;

  private MenuItem() {
  }

  public MenuItem(String id, String name, Money price) {
    this.id = id;
    this.name = name;
    this.price = price;
  }

  @Override
  public boolean equals(Object o) {
    return EqualsBuilder.reflectionEquals(this, o);
  }

  @Override
  public int hashCode() {
    return HashCodeBuilder.reflectionHashCode(this);
  }

  @Override
  public String toString() {
    return ToStringBuilder.reflectionToString(this);
  }

  public String getId() {
    return id;
  }

  public void setId(String id) {
    this.id = id;
  }

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  public Money getPrice() {
    return price;
  }

  public void setPrice(Money price) {
    this.price = price;
  }
}


// Node: getBody
package net.chrisrichardson.ftgo.restaurantservice.web;

public class CreateRestaurantResponse {
  private long id;

  public CreateRestaurantResponse() {
  }

  public long getId() {
    return id;
  }

  public void setId(long id) {
    this.id = id;
  }

  public CreateRestaurantResponse(long id) {
    this.id = id;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-restaurant-service-aws-lambda/src/main/java/net/chrisrichardson/ftgo/restaurantservice/web/CreateRestaurantResponse.java:CreateRestaurantResponse.<init>
package net.chrisrichardson.ftgo.restaurantservice.domain;

import javax.persistence.Access;
import javax.persistence.AccessType;
import javax.persistence.Embedded;
import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.Id;
import javax.persistence.Table;

@Entity
@Table(name = "restaurants")
@Access(AccessType.FIELD)
public class Restaurant {

  @Id
  @GeneratedValue
  private Long id;

  private String name;

  @Embedded
  private RestaurantMenu menu;

  private Restaurant() {
  }

  public void setId(Long id) {
    this.id = id;
  }

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }


  public Restaurant(String name, RestaurantMenu menu) {
    this.name = name;
    this.menu = menu;
  }


  public Long getId() {
    return id;
  }
}


package net.chrisrichardson.ftgo.restaurantservice.domain;

import net.chrisrichardson.ftgo.common.Money;
import org.apache.commons.lang.builder.EqualsBuilder;
import org.apache.commons.lang.builder.HashCodeBuilder;
import org.apache.commons.lang.builder.ToStringBuilder;

import javax.persistence.Access;
import javax.persistence.AccessType;
import javax.persistence.Embeddable;

@Embeddable
@Access(AccessType.FIELD)
public class MenuItem {

  private String id;
  private String name;
  private Money price;

  private MenuItem() {
  }

  public MenuItem(String id, String name, Money price) {
    this.id = id;
    this.name = name;
    this.price = price;
  }

  @Override
  public boolean equals(Object o) {
    return EqualsBuilder.reflectionEquals(this, o);
  }

  @Override
  public int hashCode() {
    return HashCodeBuilder.reflectionHashCode(this);
  }

  @Override
  public String toString() {
    return ToStringBuilder.reflectionToString(this);
  }

  public String getId() {
    return id;
  }

  public void setId(String id) {
    this.id = id;
  }

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  public Money getPrice() {
    return price;
  }

  public void setPrice(Money price) {
    this.price = price;
  }
}


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

// Node: builder
// Node: Builder
// Node: emptyMap
// Node: setStatusCode
// Node: setHeaders
// Node: setObjectBody
// Node: String
// Node: getEncoder
// Node: encode
// Node: APIGatewayProxyResponseEvent
// Node: setBody
// Node: buildErrorResponse
// Node: valueOf
// Node: getCode
// Node: applicationJsonHeaders
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

// Node: getPathParameters
package net.chrisrichardson.ftgo.restaurantservice.aws;

public class AwsLambdaError {
  private String type;
  private String code;
  private String requestId;
  private String message;

  public AwsLambdaError() {
  }

  public AwsLambdaError(String type, String code, String requestId, String message) {
    this.type = type;
    this.code = code;
    this.requestId = requestId;
    this.message = message;
  }

  public String getType() {
    return type;
  }

  public String getCode() {
    return code;
  }

  public String getRequestId() {
    return requestId;
  }

  public String getMessage() {
    return message;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-restaurant-service-aws-lambda/src/main/java/net/chrisrichardson/ftgo/restaurantservice/aws/AwsLambdaError.java:AwsLambdaError.<init>
// Node: AwsLambdaError
package net.chrisrichardson.ftgo.restaurantservice.aws;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import com.amazonaws.services.lambda.runtime.events.APIGatewayProxyRequestEvent;
import com.amazonaws.services.lambda.runtime.events.APIGatewayProxyResponseEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import static net.chrisrichardson.ftgo.restaurantservice.aws.ApiGatewayResponse.buildErrorResponse;


public abstract class AbstractHttpHandler
        implements RequestHandler<APIGatewayProxyRequestEvent, APIGatewayProxyResponseEvent> {

  private Logger log = LoggerFactory.getLogger(this.getClass());

  @Override
  public APIGatewayProxyResponseEvent handleRequest(APIGatewayProxyRequestEvent input, Context context) {
    log.debug("Got request: {}", input);
    try {
      beforeHandling(input, context);
      return handleHttpRequest(input, context);
    } catch (Exception e) {
      log.error("Error handling request id: {}", context.getAwsRequestId(), e);
      return buildErrorResponse(new AwsLambdaError(
              "Internal Server Error",
              "500",
              context.getAwsRequestId(),
              "Error handling request: " + context.getAwsRequestId() + " " + input.toString()));
    }
  }

  protected void beforeHandling(APIGatewayProxyRequestEvent request, Context context) {
    // do nothing
  }

  protected abstract APIGatewayProxyResponseEvent handleHttpRequest(APIGatewayProxyRequestEvent request, Context context);
}


// Node: handleRequest
// Node: beforeHandling
// Node: handleHttpRequest
// Node: getAwsRequestId
package net.chrisrichardson.ftgo.restaurantservice.lambda;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.events.APIGatewayProxyRequestEvent;
import com.amazonaws.services.lambda.runtime.events.APIGatewayProxyResponseEvent;
import io.eventuate.common.json.mapper.JSonMapper;
import net.chrisrichardson.ftgo.restaurantservice.aws.ApiGatewayResponse;
import net.chrisrichardson.ftgo.restaurantservice.domain.Restaurant;
import net.chrisrichardson.ftgo.restaurantservice.domain.RestaurantService;
import net.chrisrichardson.ftgo.restaurantservice.domain.CreateRestaurantRequest;
import net.chrisrichardson.ftgo.restaurantservice.web.CreateRestaurantResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;

import static net.chrisrichardson.ftgo.restaurantservice.aws.ApiGatewayResponse.applicationJsonHeaders;

@Configuration
@Import(RestaurantServiceLambdaConfiguration.class)
public class CreateRestaurantRequestHandler extends AbstractAutowiringHttpRequestHandler {

  @Autowired
  private RestaurantService restaurantService;

  @Override
  protected Class<?> getApplicationContextClass() {
    return CreateRestaurantRequestHandler.class;
  }

  @Override
  protected APIGatewayProxyResponseEvent handleHttpRequest(APIGatewayProxyRequestEvent request, Context context) {

    CreateRestaurantRequest crr = JSonMapper.fromJson(request.getBody(), CreateRestaurantRequest.class);

    Restaurant rest = restaurantService.create(crr);

    return ApiGatewayResponse.builder()
            .setStatusCode(200)
            .setObjectBody(new CreateRestaurantResponse(rest.getId()))
            .setHeaders(applicationJsonHeaders())
            .build();

  }
}


package net.chrisrichardson.ftgo.restaurantservice.lambda;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.events.APIGatewayProxyRequestEvent;
import com.amazonaws.services.lambda.runtime.events.APIGatewayProxyResponseEvent;
import net.chrisrichardson.ftgo.restaurantservice.aws.ApiGatewayResponse;
import net.chrisrichardson.ftgo.restaurantservice.aws.AwsLambdaError;
import net.chrisrichardson.ftgo.restaurantservice.domain.Restaurant;
import net.chrisrichardson.ftgo.restaurantservice.domain.RestaurantService;
import org.springframework.beans.factory.annotation.Autowired;

import java.util.Optional;

import static net.chrisrichardson.ftgo.restaurantservice.aws.ApiGatewayResponse.applicationJsonHeaders;
import static net.chrisrichardson.ftgo.restaurantservice.aws.ApiGatewayResponse.buildErrorResponse;

public class FindRestaurantRequestHandler extends AbstractAutowiringHttpRequestHandler {

  @Autowired
  private RestaurantService restaurantService;

  @Override
  protected Class<?> getApplicationContextClass() {
    return CreateRestaurantRequestHandler.class;
  }

  @Override
  protected APIGatewayProxyResponseEvent handleHttpRequest(APIGatewayProxyRequestEvent request, Context context) {
    long restaurantId;
    try {
      restaurantId = Long.parseLong(request.getPathParameters().get("restaurantId"));
    } catch (NumberFormatException e) {
      return makeBadRequestResponse(context);
    }

    Optional<Restaurant> possibleRestaurant = restaurantService.findById(restaurantId);

    return possibleRestaurant
            .map(this::makeGetRestaurantResponse)
            .orElseGet(() -> makeRestaurantNotFoundResponse(context, restaurantId));

  }

  private APIGatewayProxyResponseEvent makeBadRequestResponse(Context context) {
    return buildErrorResponse(new AwsLambdaError(
            "Bad response",
            "400",
            context.getAwsRequestId(),
            "bad response"));
  }

  private APIGatewayProxyResponseEvent makeRestaurantNotFoundResponse(Context context, long restaurantId) {
    return buildErrorResponse(new AwsLambdaError(
                    "No entity found",
                    "404",
                    context.getAwsRequestId(),
                    "Found no restaurant with id " + restaurantId));
  }

  private  APIGatewayProxyResponseEvent makeGetRestaurantResponse(Restaurant restaurant) {
    return ApiGatewayResponse.builder()
                    .setStatusCode(200)
                    .setObjectBody(new GetRestaurantResponse(restaurant.getName()))
                    .setHeaders(applicationJsonHeaders())
                    .build();
  }


}


// Node: makeBadRequestResponse
// Node: makeRestaurantNotFoundResponse
package net.chrisrichardson.ftgo.deliveryservice.api.web;

public class DeliveryInfo {

  private long id;
  private DeliveryState state;

  public DeliveryInfo() {
  }

  public DeliveryInfo(long id, DeliveryState state) {

    this.id = id;
    this.state = state;
  }

  public long getId() {
    return id;
  }

  public void setId(long id) {
    this.id = id;
  }

  public DeliveryState getState() {
    return state;
  }

  public void setState(DeliveryState state) {
    this.state = state;
  }
}


package net.chrisrichardson.ftgo.orderservice.sagas.reviseorder;

import io.eventuate.tram.commands.consumer.CommandWithDestination;
import io.eventuate.tram.sagas.simpledsl.SimpleSaga;
import net.chrisrichardson.ftgo.accountservice.api.AccountingServiceChannels;
import net.chrisrichardson.ftgo.orderservice.api.OrderServiceChannels;
import net.chrisrichardson.ftgo.orderservice.sagaparticipants.BeginReviseOrderCommand;
import net.chrisrichardson.ftgo.orderservice.sagaparticipants.BeginReviseOrderReply;
import net.chrisrichardson.ftgo.kitchenservice.api.BeginReviseTicketCommand;
import net.chrisrichardson.ftgo.orderservice.sagaparticipants.ConfirmReviseOrderCommand;
import net.chrisrichardson.ftgo.accountservice.api.ReviseAuthorization;
import net.chrisrichardson.ftgo.orderservice.sagaparticipants.UndoBeginReviseOrderCommand;
import net.chrisrichardson.ftgo.kitchenservice.api.ConfirmReviseTicketCommand;
import net.chrisrichardson.ftgo.kitchenservice.api.KitchenServiceChannels;
import net.chrisrichardson.ftgo.kitchenservice.api.UndoBeginReviseTicketCommand;
import io.eventuate.tram.sagas.orchestration.SagaDefinition;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.annotation.PostConstruct;

import static io.eventuate.tram.commands.consumer.CommandWithDestinationBuilder.send;

public class ReviseOrderSaga implements SimpleSaga<ReviseOrderSagaData> {

  private Logger logger = LoggerFactory.getLogger(getClass());

  private SagaDefinition<ReviseOrderSagaData> sagaDefinition;

  @PostConstruct
  public void initializeSagaDefinition() {
    sagaDefinition = step()
            .invokeParticipant(this::beginReviseOrder)
            .onReply(BeginReviseOrderReply.class, this::handleBeginReviseOrderReply)
            .withCompensation(this::undoBeginReviseOrder)
            .step()
            .invokeParticipant(this::beginReviseTicket)
            .withCompensation(this::undoBeginReviseTicket)
            .step()
            .invokeParticipant(this::reviseAuthorization)
            .step()
            .invokeParticipant(this::confirmTicketRevision)
            .step()
            .invokeParticipant(this::confirmOrderRevision)
            .build();
  }

  private void handleBeginReviseOrderReply(ReviseOrderSagaData data, BeginReviseOrderReply reply) {
    logger.info("ƒ order total: {}", reply.getRevisedOrderTotal());
    data.setRevisedOrderTotal(reply.getRevisedOrderTotal());
  }

  @Override
  public SagaDefinition<ReviseOrderSagaData> getSagaDefinition() {
    return sagaDefinition;
  }

  private CommandWithDestination confirmOrderRevision(ReviseOrderSagaData data) {
    return send(new ConfirmReviseOrderCommand(data.getOrderId(), data.getOrderRevision()))
            .to(OrderServiceChannels.COMMAND_CHANNEL)
            .build();

  }

  private CommandWithDestination confirmTicketRevision(ReviseOrderSagaData data) {
    return send(new ConfirmReviseTicketCommand(data.getRestaurantId(), data.getOrderId(), data.getOrderRevision().getRevisedOrderLineItems()))
            .to(KitchenServiceChannels.COMMAND_CHANNEL)
            .build();

  }

  private CommandWithDestination reviseAuthorization(ReviseOrderSagaData data) {
    return send(new ReviseAuthorization(data.getConsumerId(), data.getOrderId(), data.getRevisedOrderTotal()))
            .to(AccountingServiceChannels.accountingServiceChannel)
            .build();

  }

  private CommandWithDestination undoBeginReviseTicket(ReviseOrderSagaData data) {
    return send(new UndoBeginReviseTicketCommand(data.getRestaurantId(), data.getOrderId()))
            .to(KitchenServiceChannels.COMMAND_CHANNEL)
            .build();

  }

  private CommandWithDestination beginReviseTicket(ReviseOrderSagaData data) {
    return send(new BeginReviseTicketCommand(data.getRestaurantId(), data.getOrderId(), data.getOrderRevision().getRevisedOrderLineItems()))
            .to(KitchenServiceChannels.COMMAND_CHANNEL)
            .build();

  }

  private CommandWithDestination undoBeginReviseOrder(ReviseOrderSagaData data) {
    return send(new UndoBeginReviseOrderCommand(data.getOrderId()))
            .to(OrderServiceChannels.COMMAND_CHANNEL)
            .build();
  }

  private CommandWithDestination beginReviseOrder(ReviseOrderSagaData data) {
    return send(new BeginReviseOrderCommand(data.getOrderId(), data.getOrderRevision()))
            .to(OrderServiceChannels.COMMAND_CHANNEL)
            .build();

  }



}


// Node: getSagaDefinition
package net.chrisrichardson.ftgo.orderservice.sagas.createorder;

import io.eventuate.tram.sagas.orchestration.SagaDefinition;
import io.eventuate.tram.sagas.simpledsl.SimpleSaga;
import net.chrisrichardson.ftgo.orderservice.sagaparticipants.*;
import net.chrisrichardson.ftgo.kitchenservice.api.CreateTicketReply;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class CreateOrderSaga implements SimpleSaga<CreateOrderSagaState> {


  private Logger logger = LoggerFactory.getLogger(getClass());

  private SagaDefinition<CreateOrderSagaState> sagaDefinition;

  public CreateOrderSaga(OrderServiceProxy orderService, ConsumerServiceProxy consumerService, KitchenServiceProxy kitchenService,
                         AccountingServiceProxy accountingService) {
    this.sagaDefinition =
             step()
              .withCompensation(orderService.reject, CreateOrderSagaState::makeRejectOrderCommand)
            .step()
              .invokeParticipant(consumerService.validateOrder, CreateOrderSagaState::makeValidateOrderByConsumerCommand)
            .step()
              .invokeParticipant(kitchenService.create, CreateOrderSagaState::makeCreateTicketCommand)
              .onReply(CreateTicketReply.class, CreateOrderSagaState::handleCreateTicketReply)
              .withCompensation(kitchenService.cancel, CreateOrderSagaState::makeCancelCreateTicketCommand)
            .step()
                .invokeParticipant(accountingService.authorize, CreateOrderSagaState::makeAuthorizeCommand)
            .step()
              .invokeParticipant(kitchenService.confirmCreate, CreateOrderSagaState::makeConfirmCreateTicketCommand)
            .step()
              .invokeParticipant(orderService.approve, CreateOrderSagaState::makeApproveOrderCommand)
            .build();

  }


  @Override
  public SagaDefinition<CreateOrderSagaState> getSagaDefinition() {
    return sagaDefinition;
  }


}


package net.chrisrichardson.ftgo.orderservice.sagas.cancelorder;

import io.eventuate.tram.commands.consumer.CommandWithDestination;
import io.eventuate.tram.sagas.orchestration.SagaDefinition;
import io.eventuate.tram.sagas.simpledsl.SimpleSaga;
import net.chrisrichardson.ftgo.accountservice.api.AccountingServiceChannels;
import net.chrisrichardson.ftgo.accountservice.api.ReverseAuthorizationCommand;
import net.chrisrichardson.ftgo.orderservice.api.OrderServiceChannels;
import net.chrisrichardson.ftgo.orderservice.sagaparticipants.BeginCancelCommand;
import net.chrisrichardson.ftgo.orderservice.sagaparticipants.ConfirmCancelOrderCommand;
import net.chrisrichardson.ftgo.orderservice.sagaparticipants.UndoBeginCancelCommand;
import net.chrisrichardson.ftgo.kitchenservice.api.BeginCancelTicketCommand;
import net.chrisrichardson.ftgo.kitchenservice.api.ConfirmCancelTicketCommand;
import net.chrisrichardson.ftgo.kitchenservice.api.KitchenServiceChannels;
import net.chrisrichardson.ftgo.kitchenservice.api.UndoBeginCancelTicketCommand;
import org.springframework.util.Assert;

import javax.annotation.PostConstruct;

import static io.eventuate.tram.commands.consumer.CommandWithDestinationBuilder.send;

public class CancelOrderSaga implements SimpleSaga<CancelOrderSagaData> {



  private SagaDefinition<CancelOrderSagaData> sagaDefinition;


  @PostConstruct
  public void initializeSagaDefinition() {
    sagaDefinition = step()
            .invokeParticipant(this::beginCancel)
            .withCompensation(this::undoBeginCancel)
            .step()
            .invokeParticipant(this::beginCancelTicket)
            .withCompensation(this::undoBeginCancelTicket)
            .step()
            .invokeParticipant(this::reverseAuthorization)
            .step()
            .invokeParticipant(this::confirmTicketCancel)
            .step()
            .invokeParticipant(this::confirmOrderCancel)
            .build();

  }

  private CommandWithDestination confirmOrderCancel(CancelOrderSagaData data) {
    return send(new ConfirmCancelOrderCommand(data.getOrderId()))
            .to(OrderServiceChannels.COMMAND_CHANNEL)
            .build();

  }

  private CommandWithDestination confirmTicketCancel(CancelOrderSagaData data) {
    return send(new ConfirmCancelTicketCommand(data.getRestaurantId(), data.getOrderId()))
            .to(KitchenServiceChannels.COMMAND_CHANNEL)
            .build();

  }

  private CommandWithDestination reverseAuthorization(CancelOrderSagaData data) {
    return send(new ReverseAuthorizationCommand(data.getConsumerId(), data.getOrderId(), data.getOrderTotal()))
            .to(AccountingServiceChannels.accountingServiceChannel)
            .build();

  }

  private CommandWithDestination undoBeginCancelTicket(CancelOrderSagaData data) {
    return send(new UndoBeginCancelTicketCommand(data.getRestaurantId(), data.getOrderId()))
            .to(KitchenServiceChannels.COMMAND_CHANNEL)
            .build();

  }

  private CommandWithDestination beginCancelTicket(CancelOrderSagaData data) {
    return send(new BeginCancelTicketCommand(data.getRestaurantId(), (long) data.getOrderId()))
            .to(KitchenServiceChannels.COMMAND_CHANNEL)
            .build();

  }

  private CommandWithDestination undoBeginCancel(CancelOrderSagaData data) {
    return send(new UndoBeginCancelCommand(data.getOrderId()))
            .to(OrderServiceChannels.COMMAND_CHANNEL)
            .build();
  }

  private CommandWithDestination beginCancel(CancelOrderSagaData data) {
    return send(new BeginCancelCommand(data.getOrderId()))
            .to(OrderServiceChannels.COMMAND_CHANNEL)
            .build();
  }


  @Override
  public SagaDefinition<CancelOrderSagaData> getSagaDefinition() {
    Assert.notNull(sagaDefinition);
    return sagaDefinition;
  }



}


// Node: notNull
package net.chrisrichardson.ftgo.orderservice.domain;

import io.eventuate.tram.events.common.DomainEvent;
import org.springframework.util.Assert;

import java.util.Arrays;
import java.util.LinkedList;
import java.util.List;

public class Result {


  private final List<DomainEvent> events;
  private Boolean allowed;

  public List<DomainEvent> getEvents() {
    return events;
  }

  public Result(List<DomainEvent> events, Boolean allowed) {
    this.events = events;
    this.allowed = allowed;
  }

  public boolean isWhatIsThisCalled() {
    return allowed;
  }

  public static Builder build() {
    return new Builder();
  }

  public static class Builder {
    private List<DomainEvent> events = new LinkedList<>();
    private Boolean allowed;

    public Builder withEvents(DomainEvent... events) {
      Arrays.stream(events).forEach(e -> this.events.add(e));
      return this;
    }

    public Builder pending() {
      this.allowed = false;
      return this;
    }

    public Result build() {
      Assert.notNull(allowed);
      return new Result(events, allowed);
    }

    public Builder allowed() {
      this.allowed = false;
      return this;
    }
  }
}


// Node: getEvents
// Node: Result
package net.chrisrichardson.ftgo.orderservice.domain;

import io.eventuate.tram.events.aggregates.ResultWithDomainEvents;
import net.chrisrichardson.ftgo.common.Address;
import net.chrisrichardson.ftgo.common.Money;
import net.chrisrichardson.ftgo.common.UnsupportedStateTransitionException;
import net.chrisrichardson.ftgo.orderservice.api.events.*;

import javax.persistence.*;
import java.util.List;

import static net.chrisrichardson.ftgo.orderservice.api.events.OrderState.APPROVED;
import static net.chrisrichardson.ftgo.orderservice.api.events.OrderState.APPROVAL_PENDING;
import static net.chrisrichardson.ftgo.orderservice.api.events.OrderState.REJECTED;
import static net.chrisrichardson.ftgo.orderservice.api.events.OrderState.REVISION_PENDING;
import static java.util.Collections.emptyList;
import static java.util.Collections.singletonList;

@Entity
@Table(name = "orders")
@Access(AccessType.FIELD)
public class Order {

  public static ResultWithDomainEvents<Order, OrderDomainEvent>
  createOrder(long consumerId, Restaurant restaurant, DeliveryInformation deliveryInformation, List<OrderLineItem> orderLineItems) {
    Order order = new Order(consumerId, restaurant.getId(), deliveryInformation, orderLineItems);
    List<OrderDomainEvent> events = singletonList(new OrderCreatedEvent(
            new OrderDetails(consumerId, restaurant.getId(), orderLineItems,
                    order.getOrderTotal()),
            deliveryInformation.getDeliveryAddress(),
            restaurant.getName()));
    return new ResultWithDomainEvents<>(order, events);
  }

  @Id
  @GeneratedValue
  private Long id;

  @Version
  private Long version;

  @Enumerated(EnumType.STRING)
  private OrderState state;

  private Long consumerId;
  private Long restaurantId;

  @Embedded
  private OrderLineItems orderLineItems;

  @Embedded
  private DeliveryInformation deliveryInformation;

  @Embedded
  private PaymentInformation paymentInformation;

  @Embedded
  private Money orderMinimum = new Money(Integer.MAX_VALUE);

  private Order() {
  }

  public Order(long consumerId, long restaurantId, DeliveryInformation deliveryInformation, List<OrderLineItem> orderLineItems) {
    this.consumerId = consumerId;
    this.restaurantId = restaurantId;
    this.deliveryInformation = deliveryInformation;
    this.orderLineItems = new OrderLineItems(orderLineItems);
    this.state = APPROVAL_PENDING;
  }

  public Long getId() {
    return id;
  }

  public void setId(Long id) {
    this.id = id;
  }

  public DeliveryInformation getDeliveryInformation() {
    return deliveryInformation;
  }

  public Money getOrderTotal() {
    return orderLineItems.orderTotal();
  }

  public List<OrderDomainEvent> cancel() {
    switch (state) {
      case APPROVED:
        this.state = OrderState.CANCEL_PENDING;
        return emptyList();
      default:
        throw new UnsupportedStateTransitionException(state);
    }
  }

  public List<OrderDomainEvent> undoPendingCancel() {
    switch (state) {
      case CANCEL_PENDING:
        this.state = OrderState.APPROVED;
        return emptyList();
      default:
        throw new UnsupportedStateTransitionException(state);
    }
  }

  public List<OrderDomainEvent> noteCancelled() {
    switch (state) {
      case CANCEL_PENDING:
        this.state = OrderState.CANCELLED;
        return singletonList(new OrderCancelled());
      default:
        throw new UnsupportedStateTransitionException(state);
    }
  }

  public List<OrderDomainEvent> noteApproved() {
    switch (state) {
      case APPROVAL_PENDING:
        this.state = APPROVED;
        return singletonList(new OrderAuthorized());
      default:
        throw new UnsupportedStateTransitionException(state);
    }

  }

  public List<OrderDomainEvent> noteRejected() {
    switch (state) {
      case APPROVAL_PENDING:
        this.state = REJECTED;
        return singletonList(new OrderRejected());

      default:
        throw new UnsupportedStateTransitionException(state);
    }

  }


  public List<OrderDomainEvent> noteReversingAuthorization() {
    return null;
  }

  public ResultWithDomainEvents<LineItemQuantityChange, OrderDomainEvent> revise(OrderRevision orderRevision) {
    switch (state) {

      case APPROVED:
        LineItemQuantityChange change = orderLineItems.lineItemQuantityChange(orderRevision);
        if (change.newOrderTotal.isGreaterThanOrEqual(orderMinimum)) {
          throw new OrderMinimumNotMetException();
        }
        this.state = REVISION_PENDING;
        return new ResultWithDomainEvents<>(change, singletonList(new OrderRevisionProposed(orderRevision, change.currentOrderTotal, change.newOrderTotal)));

      default:
        throw new UnsupportedStateTransitionException(state);
    }
  }

  public List<OrderDomainEvent> rejectRevision() {
    switch (state) {
      case REVISION_PENDING:
        this.state = APPROVED;
        return emptyList();
      default:
        throw new UnsupportedStateTransitionException(state);
    }
  }

  public List<OrderDomainEvent> confirmRevision(OrderRevision orderRevision) {
    switch (state) {
      case REVISION_PENDING:
        LineItemQuantityChange licd = orderLineItems.lineItemQuantityChange(orderRevision);

        orderRevision.getDeliveryInformation().ifPresent(newDi -> this.deliveryInformation = newDi);

        if (orderRevision.getRevisedOrderLineItems() != null && orderRevision.getRevisedOrderLineItems().size() > 0) {
          orderLineItems.updateLineItems(orderRevision);
        }

        this.state = APPROVED;
        return singletonList(new OrderRevised(orderRevision, licd.currentOrderTotal, licd.newOrderTotal));
      default:
        throw new UnsupportedStateTransitionException(state);
    }
  }


  public Long getVersion() {
    return version;
  }

  public List<OrderLineItem> getLineItems() {
    return orderLineItems.getLineItems();
  }

  public OrderState getState() {
    return state;
  }

  public long getRestaurantId() {
    return restaurantId;
  }


  public Long getConsumerId() {
    return consumerId;
  }
}



package net.chrisrichardson.ftgo.orderservice.domain;

import net.chrisrichardson.ftgo.common.Money;
import org.apache.commons.lang.builder.EqualsBuilder;
import org.apache.commons.lang.builder.HashCodeBuilder;
import org.apache.commons.lang.builder.ToStringBuilder;

import javax.persistence.Access;
import javax.persistence.AccessType;
import javax.persistence.Embeddable;

@Embeddable
@Access(AccessType.FIELD)
public class MenuItem {

  private String id;
  private String name;
  private Money price;

  private MenuItem() {
  }

  public MenuItem(String id, String name, Money price) {
    this.id = id;
    this.name = name;
    this.price = price;
  }

  @Override
  public boolean equals(Object o) {
    return EqualsBuilder.reflectionEquals(this, o);
  }

  @Override
  public int hashCode() {
    return HashCodeBuilder.reflectionHashCode(this);
  }

  @Override
  public String toString() {
    return ToStringBuilder.reflectionToString(this);
  }

  public String getId() {
    return id;
  }

  public void setId(String id) {
    this.id = id;
  }

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  public Money getPrice() {
    return price;
  }

  public void setPrice(Money price) {
    this.price = price;
  }
}


package net.chrisrichardson.ftgo.kitchenservice.domain;

import net.chrisrichardson.ftgo.common.Money;
import org.apache.commons.lang.builder.EqualsBuilder;
import org.apache.commons.lang.builder.HashCodeBuilder;
import org.apache.commons.lang.builder.ToStringBuilder;

import javax.persistence.Access;
import javax.persistence.AccessType;
import javax.persistence.Embeddable;

@Embeddable
@Access(AccessType.FIELD)
public class MenuItem {

  private String id;
  private String name;
  private Money price;

  private MenuItem() {
  }

  public MenuItem(String id, String name, Money price) {
    this.id = id;
    this.name = name;
    this.price = price;
  }

  @Override
  public boolean equals(Object o) {
    return EqualsBuilder.reflectionEquals(this, o);
  }

  @Override
  public int hashCode() {
    return HashCodeBuilder.reflectionHashCode(this);
  }

  @Override
  public String toString() {
    return ToStringBuilder.reflectionToString(this);
  }

  public String getId() {
    return id;
  }

  public void setId(String id) {
    this.id = id;
  }

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  public Money getPrice() {
    return price;
  }

  public void setPrice(Money price) {
    this.price = price;
  }
}


