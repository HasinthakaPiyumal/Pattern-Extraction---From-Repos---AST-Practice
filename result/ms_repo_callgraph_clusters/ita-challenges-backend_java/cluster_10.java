// Cluster 10

package com.itachallenge.document;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.openfeign.EnableFeignClients;

@SpringBootApplication
@EnableDiscoveryClient
@EnableFeignClients(basePackages = "com.itachallenge.document.proxy")
public class App {

    public static void main(String[] args) {
        SpringApplication.run(App.class, args);
    }
}

// Node: main
// Node: run
package com.itachallenge;

import com.itachallenge.githubcore.config.GithubServiceConfig;
import io.swagger.v3.oas.annotations.OpenAPIDefinition;
import io.swagger.v3.oas.annotations.info.Info;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.context.annotation.Import;

@SpringBootApplication
@Import(GithubServiceConfig.class)
@EnableDiscoveryClient
@OpenAPIDefinition(info = @Info(title = "Ita Backend User", version = "1.0", description = "Description"))
public class App {

    public static void main(String[] args) {
        SpringApplication.run(App.class, args);
    }
}


package com.itachallenge;

import org.junit.jupiter.api.Test;

class AppTest {
    @Test
    void main_runs() {
        App.main(new String[]{"--spring.main.web-application-type=none"});
    }
}

// Node: main_runs
package com.itachallenge;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;

@SpringBootApplication
@EnableDiscoveryClient
public class App {

    public static void main(String[] args) {
        SpringApplication.run(App.class, args);
    }
}

package com.itachallenge.auth;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.context.annotation.ComponentScan;

@SpringBootApplication
@EnableDiscoveryClient
@ComponentScan(basePackages = {
        "com.itachallenge.auth",
        "com.itachallenge.jwtcore"
})
public class App {
    public static void main(String[] args) {
        SpringApplication.run(App.class, args);
    }
}

package com.itachallenge.mock;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class App {

    public static void main(String[] args) {
        SpringApplication.run(App.class, args);
    }
}

