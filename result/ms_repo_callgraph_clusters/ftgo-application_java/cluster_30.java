// Cluster 30

package net.chrisrichardson.ftgo.restaurantservice;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.eventuate.common.json.mapper.JSonMapper;
import io.eventuate.tram.spring.jdbckafka.TramJdbcKafkaConfiguration;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Import;
import org.springframework.context.annotation.Primary;

@SpringBootApplication
@Import(TramJdbcKafkaConfiguration.class)
public class RestaurantServiceMain {

  @Bean
  @Primary // conflicts with _halObjectMapper
  public ObjectMapper objectMapper() {
    return JSonMapper.objectMapper;
  }

  public static void main(String[] args) {
    SpringApplication.run(RestaurantServiceMain.class, args);
  }

}


// Node: main
// Node: run
package net.chrisrichardson.ftgo.apiagateway;


import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.ComponentScan;

@SpringBootApplication
@ComponentScan
public class ApiGatewayApplication {

  public static void main(String[] args) {
    SpringApplication.run(ApiGatewayApplication.class, args);
  }
}



package net.chrisrichardson.ftgo.restaurantservice.lambda;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.events.APIGatewayProxyRequestEvent;
import net.chrisrichardson.ftgo.restaurantservice.aws.AbstractHttpHandler;
import org.springframework.boot.SpringApplication;
import org.springframework.context.ApplicationContext;
import org.springframework.context.ConfigurableApplicationContext;

import java.util.concurrent.locks.ReentrantReadWriteLock;

public abstract class AbstractAutowiringHttpRequestHandler extends AbstractHttpHandler {

  private static ConfigurableApplicationContext ctx;
  private ReentrantReadWriteLock ctxLock = new ReentrantReadWriteLock();
  private boolean autowired = false;

  protected synchronized ApplicationContext getAppCtx() {
    ctxLock.writeLock().lock();
    try {
      if (ctx == null) {
        ctx =  SpringApplication.run(getApplicationContextClass());
      }
      return ctx;
    } finally {
      ctxLock.writeLock().unlock();
    }
  }

  protected abstract Class<?> getApplicationContextClass();

  @Override
  protected void beforeHandling(APIGatewayProxyRequestEvent request, Context context) {
    super.beforeHandling(request, context);
    if (!autowired) {
      getAppCtx().getAutowireCapableBeanFactory().autowireBean(this);
      autowired = true;
    }
  }
}


// Node: getAppCtx
// Node: writeLock
// Node: lock
// Node: getApplicationContextClass
// Node: unlock
// Node: getAutowireCapableBeanFactory
// Node: autowireBean
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


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-restaurant-service-aws-lambda/src/main/java/net/chrisrichardson/ftgo/restaurantservice/lambda/CreateRestaurantRequestHandler.java:CreateRestaurantRequestHandler.<init>
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


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-restaurant-service-aws-lambda/src/main/java/net/chrisrichardson/ftgo/restaurantservice/lambda/FindRestaurantRequestHandler.java:FindRestaurantRequestHandler.<init>
package net.chrisrichardson.ftgo.accountingservice.main;

import io.eventuate.local.java.spring.javaclient.driver.EventuateDriverConfiguration;
import io.eventuate.tram.spring.commands.producer.TramCommandProducerConfiguration;
import io.eventuate.tram.spring.jdbckafka.TramJdbcKafkaConfiguration;
import net.chrisrichardson.eventstore.examples.customersandorders.commonswagger.CommonSwaggerConfiguration;
import net.chrisrichardson.ftgo.accountingservice.messaging.AccountingMessagingConfiguration;
import net.chrisrichardson.ftgo.accountingservice.web.AccountingWebConfiguration;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;

@Configuration
@EnableAutoConfiguration
@Import({AccountingMessagingConfiguration.class, AccountingWebConfiguration.class,
        TramCommandProducerConfiguration.class,
        EventuateDriverConfiguration.class,
        TramJdbcKafkaConfiguration.class,
        CommonSwaggerConfiguration.class})
public class AccountingServiceMain {

  public static void main(String[] args) {
    SpringApplication.run(AccountingServiceMain.class, args);
  }
}


package net.chrisrichardson.ftgo.cqrs.orderhistory.main;

import io.eventuate.tram.spring.consumer.common.TramConsumerCommonConfiguration;
import io.eventuate.tram.spring.consumer.kafka.EventuateTramKafkaMessageConsumerConfiguration;
import net.chrisrichardson.eventstore.examples.customersandorders.commonswagger.CommonSwaggerConfiguration;
import net.chrisrichardson.ftgo.cqrs.orderhistory.messaging.OrderHistoryServiceMessagingConfiguration;
import net.chrisrichardson.ftgo.cqrs.orderhistory.web.OrderHistoryWebConfiguration;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Import;

@SpringBootApplication
@Import({OrderHistoryWebConfiguration.class,
        OrderHistoryServiceMessagingConfiguration.class,
        CommonSwaggerConfiguration.class,
        TramConsumerCommonConfiguration.class,
        EventuateTramKafkaMessageConsumerConfiguration.class})
public class OrderHistoryServiceMain {

  public static void main(String[] args) {
    SpringApplication.run(OrderHistoryServiceMain.class, args);
  }
}


package net.chrisrichardson.ftgo.orderservice.main;

import io.eventuate.tram.spring.jdbckafka.TramJdbcKafkaConfiguration;
import io.microservices.canvas.extractor.spring.annotations.ServiceDescription;
import io.microservices.canvas.springmvc.MicroserviceCanvasWebConfiguration;
import net.chrisrichardson.eventstore.examples.customersandorders.commonswagger.CommonSwaggerConfiguration;
import net.chrisrichardson.ftgo.orderservice.grpc.GrpcConfiguration;
import net.chrisrichardson.ftgo.orderservice.messaging.OrderServiceMessagingConfiguration;
import net.chrisrichardson.ftgo.orderservice.service.OrderCommandHandlersConfiguration;
import net.chrisrichardson.ftgo.orderservice.web.OrderWebConfiguration;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Import;

@SpringBootApplication
@Import({OrderWebConfiguration.class, OrderCommandHandlersConfiguration.class,  OrderServiceMessagingConfiguration.class,
        TramJdbcKafkaConfiguration.class, CommonSwaggerConfiguration.class, GrpcConfiguration.class,
        MicroserviceCanvasWebConfiguration.class})
@ServiceDescription(description="Manages Orders", capabilities = "Order Management")
public class OrderServiceMain {

  public static void main(String[] args) {
    SpringApplication.run(OrderServiceMain.class, args);
  }
}


package net.chrisrichardson.ftgo.deliveryservice.main;

import io.eventuate.tram.spring.jdbckafka.TramJdbcKafkaConfiguration;
import net.chrisrichardson.eventstore.examples.customersandorders.commonswagger.CommonSwaggerConfiguration;
import net.chrisrichardson.ftgo.deliveryservice.messaging.DeliveryServiceMessagingConfiguration;
import net.chrisrichardson.ftgo.deliveryservice.web.DeliveryServiceWebConfiguration;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;

@Configuration
@EnableAutoConfiguration
@Import({DeliveryServiceMessagingConfiguration.class, DeliveryServiceWebConfiguration.class,
        TramJdbcKafkaConfiguration.class, CommonSwaggerConfiguration.class
})
public class DeliveryServiceMain {

  public static void main(String[] args) {
    SpringApplication.run(DeliveryServiceMain.class, args);
  }
}


package net.chrisrichardson.ftgo.kitchenservice.main;

import io.eventuate.tram.spring.jdbckafka.TramJdbcKafkaConfiguration;
import net.chrisrichardson.eventstore.examples.customersandorders.commonswagger.CommonSwaggerConfiguration;
import net.chrisrichardson.ftgo.kitchenservice.messagehandlers.KitchenServiceMessageHandlersConfiguration;
import net.chrisrichardson.ftgo.kitchenservice.web.KitchenServiceWebConfiguration;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Import;

@SpringBootApplication
@Import({KitchenServiceWebConfiguration.class,
        KitchenServiceMessageHandlersConfiguration.class,
        TramJdbcKafkaConfiguration.class,
        CommonSwaggerConfiguration.class})
public class KitchenServiceMain {

  public static void main(String[] args) {
    SpringApplication.run(KitchenServiceMain.class, args);
  }
}


package net.chrisrichardson.ftgo.consumerservice.main;

import io.eventuate.tram.spring.jdbckafka.TramJdbcKafkaConfiguration;
import net.chrisrichardson.eventstore.examples.customersandorders.commonswagger.CommonSwaggerConfiguration;
import net.chrisrichardson.ftgo.consumerservice.web.ConsumerWebConfiguration;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Import;

@SpringBootApplication
@Import({ConsumerWebConfiguration.class, TramJdbcKafkaConfiguration.class, CommonSwaggerConfiguration.class})
public class ConsumerServiceMain {

  public static void main(String[] args) {
    SpringApplication.run(ConsumerServiceMain.class, args);
  }
}


