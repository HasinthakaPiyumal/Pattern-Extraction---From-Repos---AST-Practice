// Cluster 29

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


// Node: objectMapper
package net.chrisrichardson.ftgo.orderservice.web;

import brave.sampler.Sampler;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.eventuate.common.json.mapper.JSonMapper;
import net.chrisrichardson.ftgo.orderservice.domain.OrderServiceWithRepositoriesConfiguration;
import org.springframework.context.annotation.*;

@Configuration
@ComponentScan
@Import(OrderServiceWithRepositoriesConfiguration.class)
public class OrderWebConfiguration {

  @Bean
  @Primary
  public ObjectMapper objectMapper() {
    return JSonMapper.objectMapper;
  }

  @Bean
  public Sampler defaultSampler() {
    return Sampler.ALWAYS_SAMPLE;
  }

}


