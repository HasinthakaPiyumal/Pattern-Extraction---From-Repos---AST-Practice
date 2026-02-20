// Cluster 7

package com.example.springcloud.gateway;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class GatewayServiceApplication {

	public static void main(String[] args) {
		SpringApplication.run(GatewayServiceApplication.class, args);
	}

}


// Node: main
// Node: run
package io.javatab.microservices.core.course;


import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.context.annotation.ComponentScan;


@SpringBootApplication
@ComponentScan({"io.javatab"})
public class CourseServiceApplication {

	private static final Logger LOG = LoggerFactory.getLogger(CourseServiceApplication.class);

	public static void main(String[] args) {
		ConfigurableApplicationContext ctx = SpringApplication.run(CourseServiceApplication.class, args);

		String postgresUri = ctx.getEnvironment().getProperty("spring.datasource.url");
		LOG.info("Connected to Postgres: " + postgresUri);
	}

}


// Node: getEnvironment
// Node: getProperty
package io.javatab.microservices.composite.course;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.web.client.RestTemplate;

@SpringBootApplication
@ComponentScan({"io.javatab"})
public class CourseCompositeServiceApplication {

	public static void main(String[] args) {
		SpringApplication.run(CourseCompositeServiceApplication.class, args);
	}

}


package io.javatab.microservices.core.review;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.context.annotation.ComponentScan;

@SpringBootApplication
@ComponentScan({"io.javatab"})
public class ReviewServiceApplication {

	private static final Logger logger = LoggerFactory.getLogger(ReviewServiceApplication.class);

	public static void main(String[] args) {
		ConfigurableApplicationContext ctx = SpringApplication.run(ReviewServiceApplication.class, args);

		String mongoDbUri = ctx.getEnvironment().getProperty("spring.data.mongodb.uri");
        logger.info("Connected to MongoDb ===> {}", mongoDbUri);
	}

}


