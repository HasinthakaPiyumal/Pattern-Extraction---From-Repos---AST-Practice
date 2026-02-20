// Cluster 8

package com.cognizant.accountservice.repository;

import java.util.Date;
import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import com.cognizant.accountservice.model.Statement;

@Repository
public interface StatementRepository extends JpaRepository<Statement, Long> {
	@Query(nativeQuery = true, value = "SELECT * from STATEMENT s WHERE (s.source_Id = :accountId or s.target_Id = :accountId) and (date between :startDate and :endDate) order by date desc ")
	List<Statement> findStatementByAccountId(@Param(value = "accountId") long accountId,Date startDate,Date endDate);
}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Account-MS/src/main/java/com/cognizant/accountservice/repository/StatementRepository.java:StatementRepository.<init>
// Node: Query
// Node: WHERE
// Node: and
// Node: findStatementByAccountId
// Node: Param
package com.cognizant.accountservice.repository;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import com.cognizant.accountservice.model.Account;


@Repository
public interface AccountRepository extends JpaRepository<Account, Long> {

	@Query(nativeQuery = true, value = "SELECT * from ACCOUNT a WHERE a.account_Id = :accountId")
	Account findByAccountId(@Param(value = "accountId") long accountId);

	List<Account> findByCustomerId(String customerId);

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Account-MS/src/main/java/com/cognizant/accountservice/repository/AccountRepository.java:AccountRepository.<init>
// Node: hasRole
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

// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Authentication-MS/src/main/java/com/cognizant/authenticationservice/securityconfig/SecurityConfigurer.java:SecurityConfigurer.<init>
// Node: EnableGlobalMethodSecurity
// Node: configure
// Node: userDetailsService
// Node: ignoring
// Node: antMatchers
// Node: csrf
// Node: disable
// Node: authorizeRequests
// Node: permitAll
// Node: anyRequest
// Node: authenticated
// Node: exceptionHandling
// Node: sessionManagement
// Node: sessionCreationPolicy
// Node: addFilterBefore
