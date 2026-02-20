// Cluster 6

package com.cognizant.authenticationservice.securityconfig;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.config.annotation.authentication.builders.AuthenticationManagerBuilder;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.builders.WebSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

import com.cognizant.authenticationservice.service.CustomerDetailsService;
import com.cognizant.authenticationservice.service.JwtRequestFilter;

@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfigurer extends WebSecurityConfigurerAdapter {

	@Autowired
	private JwtRequestFilter jwtRequestFilter;

	@Autowired
	CustomerDetailsService customerDetailsService;

	@Override
	protected void configure(AuthenticationManagerBuilder auth) throws Exception {
		super.configure(auth);
		auth.userDetailsService(customerDetailsService);

	}

	@Override
	public void configure(WebSecurity web) throws Exception {
		web.ignoring().antMatchers("/auth-ms/login", "/h2-console/**", "/validateToken", "/role/**");
	}

	@Override
	protected void configure(HttpSecurity http) throws Exception {
		http.csrf().disable().authorizeRequests().antMatchers("/auth-ms/emp").hasRole("EMPLOYEE").antMatchers("/*")
				.permitAll().anyRequest().authenticated().and().exceptionHandling().and().sessionManagement()
				.sessionCreationPolicy(SessionCreationPolicy.STATELESS);

		http.addFilterBefore(jwtRequestFilter, UsernamePasswordAuthenticationFilter.class);
	}

	@Bean
	public BCryptPasswordEncoder passwordEncoder() {
		return new BCryptPasswordEncoder();
	}

	@Override
	@Bean
	public AuthenticationManager authenticationManagerBean() throws Exception {
		return super.authenticationManagerBean();
	}
}

// Node: passwordEncoder
// Node: BCryptPasswordEncoder
// Node: authenticationManagerBean
// Node: UserRepository
// Node: Autowired
// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Authentication-MS/bin/src/main/java/com/retailbank/AuthenticationMS/service/JwtRequestFilter.class:JwtRequestFilter
// Node: src.main.java.com.retailbank.AuthenticationMS.service.CustomerDetailsService
// Node: src.main.java.com.retailbank.AuthenticationMS.service.JwtUtil
// Node: src.main.java.com.retailbank.AuthenticationMS.service.JwtRequestFilter
// Node: HttpServletRequest
// Node: HttpServletResponse
// Node: FilterChain
// Node: Component
// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Authentication-MS/bin/src/main/java/com/retailbank/AuthenticationMS/service/Validationservice.class:Validationservice
// Node: src.main.java.com.retailbank.AuthenticationMS.service.Validationservice
// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Authentication-MS/bin/src/main/java/com/retailbank/AuthenticationMS/service/JwtUtil.class:JwtUtil
// Node: Function
// Node: Claims
// Node: UserDetails
// Node: Map
// Node: Boolean
// Node: Service
// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Authentication-MS/bin/src/main/java/com/retailbank/AuthenticationMS/service/CustomerDetailsService.class:CustomerDetailsService
// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Authentication-MS/bin/src/main/java/com/retailbank/AuthenticationMS/service/LoginService.class:LoginService
// Node: src.main.java.com.retailbank.AuthenticationMS.service.LoginService
// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Authentication-MS/bin/src/main/java/com/retailbank/AuthenticationMS/securityConfig/SecurityConfigurer.class:SecurityConfigurer
// Node: JwtRequestFilter
// Node: CustomerDetailsService
// Node: src.main.java.com.retailbank.AuthenticationMS.securityConfig.SecurityConfigurer
// Node: AuthenticationManagerBuilder
// Node: WebSecurity
// Node: HttpSecurity
// Node: AuthenticationManager
// Node: EnableWebSecurity
