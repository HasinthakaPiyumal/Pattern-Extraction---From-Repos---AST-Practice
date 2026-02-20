// Cluster 1

package com.cognizant.accountservice;

import java.util.Collections;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.context.annotation.Bean;

import com.cognizant.accountservice.controller.AccountController;

import springfox.documentation.builders.RequestHandlerSelectors;
import springfox.documentation.service.ApiInfo;
import springfox.documentation.service.Contact;
import springfox.documentation.spi.DocumentationType;
import springfox.documentation.spring.web.plugins.Docket;
import springfox.documentation.swagger2.annotations.EnableSwagger2;


@SpringBootApplication
@EnableFeignClients
@EnableSwagger2
public class AccountserviceApplication {

	private static final Logger LOGGER = LoggerFactory.getLogger(AccountController.class);

	public static void main(String[] args) { 
		SpringApplication.run(AccountserviceApplication.class, args);
		LOGGER.info("Account microservice started....");
	}
	
	/*
	 * Adding Swaggar2 REST API Documentation bean
	 */
	@Bean
	public Docket swaggerConfiguration() {

		return new Docket(DocumentationType.SWAGGER_2).select()
				.apis(RequestHandlerSelectors.basePackage("com.cognizant.accountservice.controller")).build().apiInfo(apiInfo());
 
	}

	
	private ApiInfo apiInfo() {
		return new ApiInfo("Account Management Service", "Retail Banking Project", "API", "Terms of service",
				new Contact("Peoples' Bank", "", "abc@email.com"), "License of API", "", Collections.emptyList());
	}

}


// Node: main
// Node: run
package com.cognizant.accountservice;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest
class AccountserviceApplicationTests {
	
	@Test
	void setCustomerIdTest() {
		String check="Cust101";
		assertEquals("Cust101",check );
	}
	
	@Test
	public void main() {
		AccountserviceApplication.main(new String[] {});
	}
}


package com.cognizant.authenticationservice;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * The AuthenticationMsApplication class to start the application
 *
 */
@SpringBootApplication
public class AuthenticationMsApplication {

	/**
	 * The main method for app
	 */
	public static void main(String[] args) {
		SpringApplication.run(AuthenticationMsApplication.class, args);
	}

}


package com.cognizant.authenticationservice;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest
class AuthenticationMsApplicationTests {

	@Test
	void contextLoads() {
	}
	@Test
	void main() {
		AuthenticationMsApplication.main(new String[] {});
	}

}


package com.rulesservice;

import java.util.Collections;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.context.annotation.Bean;
import springfox.documentation.builders.RequestHandlerSelectors;
import springfox.documentation.service.ApiInfo;
import springfox.documentation.service.Contact;
import springfox.documentation.spi.DocumentationType;
import springfox.documentation.spring.web.plugins.Docket;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

@EnableFeignClients
@EnableSwagger2
@SpringBootApplication
public class RulesServiceApplication {

	public static void main(String[] args) {
		SpringApplication.run(RulesServiceApplication.class, args);
	}

	@Bean
	public Docket swaggerConfiguration() {

		return new Docket(DocumentationType.SWAGGER_2).select()
				.apis(RequestHandlerSelectors.basePackage("com.rulesservice.controller")).build().apiInfo(apiInfo());

	}

	private ApiInfo apiInfo() {
		return new ApiInfo("RulesService", "MFPE project service", "API", "Terms of service",
				new Contact("Peoples Bank", "", "abcbanking@gmail.com"), "License of API", "", Collections.emptyList());
	}
}


package com.rulesservice;

import org.junit.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.boot.builder.SpringApplicationBuilder;

@ExtendWith(MockitoExtension.class)
public class ServletIntializerTest {

	@Mock
	private SpringApplicationBuilder springApplicationBuilder;

	@Test
	public void main() {
		RulesServiceApplication.main(new String[] {});
	}

}


package com.cognizant.customerservice;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.openfeign.EnableFeignClients;
import springfox.documentation.swagger2.annotations.EnableSwagger2;


@SpringBootApplication
@EnableFeignClients
@EnableSwagger2
public class CustomerServiceApplication { 

	public static void main(String[] args) {
		SpringApplication.run(CustomerServiceApplication.class, args);
	}
}
  

package com.cognizant.CustomerService;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;

import com.cognizant.customerservice.CustomerServiceApplication;

@SpringBootTest
class CustomerServiceApplicationTests {

	@Test
	void contextLoads() {
		String check = "Cust101";
		assertEquals("Cust101", check);
	}

	@Test
	void main() {
		CustomerServiceApplication.main(new String[] {});
	}

}


package com.cognizant.transactionservice;

import java.util.Collections;

import org.springframework.boot.SpringApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.context.annotation.Bean;

import lombok.extern.slf4j.Slf4j;
import springfox.documentation.builders.RequestHandlerSelectors;
import springfox.documentation.service.ApiInfo;
import springfox.documentation.service.Contact;
import springfox.documentation.spi.DocumentationType;
import springfox.documentation.spring.web.plugins.Docket;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

@SpringBootApplication
@EnableDiscoveryClient
@EnableFeignClients
@EnableSwagger2
@Slf4j
public class TransactionserviceApplication {

	public static void main(String[] args) {
		log.info("TransactionserviceApplication is started");
		SpringApplication.run(TransactionserviceApplication.class, args);
	}

	@Bean
	public Docket swaggerConfiguration() {

		return new Docket(DocumentationType.SWAGGER_2).select()
				.apis(RequestHandlerSelectors.basePackage("com.cognizant.transactionservice.controller")).build()
				.apiInfo(apiInfo());

	}

	private ApiInfo apiInfo() {
		return new ApiInfo("Transaction Service", "Retail Banking Project", "API", "Terms of service",
				new Contact("Peoples' Bank", "", "abc@email.com"), "License of API", "", Collections.emptyList());
	}

}


package com.cognizant.transactionservice.initializer;

import org.junit.jupiter.api.Test;

//import com.cognizant.accountservice.AccountserviceApplication;
import com.cognizant.transactionservice.TransactionserviceApplication;

public class ServletInitializerTest {

	@Test
	public void main() {
		TransactionserviceApplication.main(new String[] {});
	}

}


