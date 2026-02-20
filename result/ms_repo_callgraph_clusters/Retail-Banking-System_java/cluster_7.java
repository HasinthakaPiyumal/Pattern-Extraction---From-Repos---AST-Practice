// Cluster 7

// Node: println
// Node: AccountCreationStatus
package com.cognizant.accountservice.controller;

import static org.mockito.Mockito.timeout;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;

import org.junit.jupiter.api.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.context.junit4.SpringRunner;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;

import com.cognizant.accountservice.feignclient.AuthFeignClient;
import com.cognizant.accountservice.feignclient.TransactionFeign;
import com.cognizant.accountservice.model.Account;
import com.cognizant.accountservice.model.AccountCreationStatus;
import com.cognizant.accountservice.model.AccountInput;
import com.cognizant.accountservice.model.AuthenticationResponse;
import com.cognizant.accountservice.repository.AccountRepository;
import com.cognizant.accountservice.service.AccountServiceImpl;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;


@RunWith(SpringRunner.class)
@SpringBootTest
@AutoConfigureMockMvc
class AccountControllerTest {

	@Autowired
	private MockMvc mockMvc;

	@MockBean
	private AuthFeignClient authFeign;

	@MockBean
	private AccountServiceImpl accountServiceImpl;

	@MockBean
	private AccountRepository accountRepository;

	@MockBean
	private TransactionFeign transactionFeign;
	

	@Test
	void getAccountTest() throws Exception {
		when(accountServiceImpl.hasPermission("token")).thenReturn(new AuthenticationResponse("", "", true));
		Account acc = new Account();
		when(accountServiceImpl.getAccount(1)).thenReturn(acc);
		mockMvc.perform(get("/getAccount/1").header("Authorization", "token")).andExpect(status().isOk());
		verify(accountServiceImpl, timeout(1)).getAccount(1);
	}
	

	@Test
	void getCustomerAccountTest() throws Exception {
		when(accountServiceImpl.hasPermission("token")).thenReturn(new AuthenticationResponse("", "", true));
		when(accountServiceImpl.getCustomerAccount("token", "cust01")).thenReturn(new ArrayList<>());
		mockMvc.perform(get("/getAccounts/cust01").header("Authorization", "token")).andExpect(status().isOk());
		verify(accountServiceImpl, timeout(1)).getCustomerAccount("token", "cust01");
	}

	@Test
	void createAccountTest() throws Exception {
		Date date = new SimpleDateFormat("dd/MM/yyyy").parse("10/09/2021");
		when(accountServiceImpl.hasEmployeePermission("token")).thenReturn(new AuthenticationResponse("emp01", "emp", true));
		Account account = new Account(1, "Cust101", 3000.0, "Savings", date, "Pulkit", null);
		when(accountServiceImpl.createAccount("Cust101", account)).thenReturn(new AccountCreationStatus(1, "Sucessfully Created"));
		mockMvc.perform(MockMvcRequestBuilders
		.post("/createAccount/Cust101")
		.content(asJsonString(account))
		.contentType(MediaType.APPLICATION_JSON).accept(MediaType.APPLICATION_JSON)
		.header("Authorization", "token")).andExpect(status().isNotAcceptable());
		verify(accountServiceImpl, timeout(1)).hasEmployeePermission("token");
	}
	
	@Test
	void checkAccountBalanceTest() throws Exception {
		when(accountServiceImpl.hasPermission("token")).thenReturn(new AuthenticationResponse("cust01", "cust", true));
		AccountInput accountIp = new AccountInput();
		Account account = new Account();
		when(accountServiceImpl.getAccount(accountIp.getAccountId())).thenReturn(account);
		mockMvc.perform(MockMvcRequestBuilders.post("/checkBalance")
		.content(asJsonString(accountIp))
		.contentType(MediaType.APPLICATION_JSON)
		.accept(MediaType.APPLICATION_JSON)
		.header("Authorization", "token")).andExpect(status().isOk());
		verify(accountServiceImpl, timeout(1)).hasPermission("token");
	}
	
	@Test
	void  getAllAccountTest() throws Exception  {
		when(accountServiceImpl.hasPermission("token")).thenReturn(new AuthenticationResponse("", "", true));
		when(accountServiceImpl.getAllAccounts()).thenReturn(new ArrayList<>());
		mockMvc.perform(get("/find").header("Authorization", "token")).andExpect(status().isOk());
		verify(accountServiceImpl, timeout(1)).getAllAccounts();
	}


	public static String asJsonString(final Object obj) throws JsonProcessingException {
			final ObjectMapper mapper = new ObjectMapper();
			final String jsonContent = mapper.writeValueAsString(obj);
			return jsonContent;

	}
}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Account-MS/src/test/java/com/cognizant/accountservice/controller/AccountControllerTest.java:AccountControllerTest.<init>
// Node: RunWith
// Node: getAccountTest
// Node: perform
// Node: header
// Node: andExpect
// Node: status
// Node: isOk
// Node: verify
// Node: timeout
// Node: getCustomerAccountTest
// Node: createAccountTest
// Node: post
// Node: content
// Node: asJsonString
// Node: contentType
// Node: accept
// Node: isNotAcceptable
// Node: checkAccountBalanceTest
// Node: getAllAccountTest
// Node: ObjectMapper
// Node: writeValueAsString
// Node: AppUser
package com.cognizant.authenticationservice;

import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.io.UnsupportedEncodingException;
import java.util.ArrayList;
import java.util.List;

import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.junit4.SpringJUnit4ClassRunner;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.context.WebApplicationContext;

import com.cognizant.authenticationservice.model.AppUser;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonMappingException;
import com.fasterxml.jackson.databind.ObjectMapper;

@SpringBootTest
@RunWith(SpringJUnit4ClassRunner.class)
public class Tests {

	public String token;

	private MockMvc mockMvc;

	@Autowired
	private WebApplicationContext wc;

	List<AppUser> employees = new ArrayList<AppUser>();
	static ObjectMapper mapper = new ObjectMapper();

	@Before
	// before testing class login should be done
	// it execute before all methods
	public void setUp() throws JsonProcessingException, Exception {
		mockMvc = MockMvcBuilders.webAppContextSetup(wc).build();
		login();
	}

	public static <T> T parseResponse(MvcResult result, Class<T> responseClass)
			throws UnsupportedEncodingException, JsonMappingException, JsonProcessingException {

		String contentAsString = result.getResponse().getContentAsString();
		return mapper.readValue(contentAsString, responseClass);

	}

//	@Test
//	public void saveEmployee() throws JsonProcessingException, Exception {
//		AppUser menu = new AppUser("111", "ba", "ba", "", "EMPLOYEE");
//		String json = mapper.writeValueAsString(menu);
//		mockMvc.perform(MockMvcRequestBuilders.post("/createUser").content(json).contentType(MediaType.APPLICATION_JSON)
//				.accept(MediaType.APPLICATION_JSON)).andExpect(status().isCreated())
//				.andExpect(MockMvcResultMatchers.jsonPath("$.userid").exists());
//	}
//
//	// save employee negative test case
//	@Test
//	public void saveEmployeeNeg() throws JsonProcessingException, Exception {
//		AppUser menu = new AppUser("111", "yam", "yam", "", "EMPLOYEE");
//		String json = mapper.writeValueAsString(menu);
//		mockMvc.perform(MockMvcRequestBuilders.post("/createUser").content(json).contentType(MediaType.APPLICATION_JSON)
//				.accept(MediaType.APPLICATION_JSON)).andExpect(status().isCreated())
//				.andExpect(MockMvcResultMatchers.jsonPath("$.userid1").doesNotExist());
//
//	}
//
	@Test
	public void login() throws JsonProcessingException, Exception {
		AppUser menu = new AppUser("EMPLOYEE101", "emp", "emp", "", "EMPLOYEE");
		String json = mapper.writeValueAsString(menu);
		MvcResult andReturn = mockMvc
				.perform(MockMvcRequestBuilders.post("/login").content(json).contentType(MediaType.APPLICATION_JSON)
						.accept(MediaType.APPLICATION_JSON))
				.andExpect(status().is2xxSuccessful()).andExpect(MockMvcResultMatchers.jsonPath("$.authToken").exists())
				.andReturn();
		AppUser response = parseResponse(andReturn, AppUser.class);
		token = response.getAuthToken();
	}
//
//	// check if token is wrong the login should not proceed
//	@Test
//	public void login2() throws JsonProcessingException, Exception {
//		AppUser menu = new AppUser("EMPLOYEE101", "emp", "emp", "", "EMPLOYEE");
//		String json = mapper.writeValueAsString(menu);
//		MvcResult andReturn = mockMvc
//				.perform(MockMvcRequestBuilders.post("/login").content(json).contentType(MediaType.APPLICATION_JSON)
//						.accept(MediaType.APPLICATION_JSON))
//				.andExpect(status().isOk()).andExpect(MockMvcResultMatchers.jsonPath("$.authToken2").doesNotExist())
//				.andReturn();
//	}
//
////before find the method is checked here	
//	@Test
//	public void getOneEmployees() throws JsonProcessingException, Exception {
//		System.err.println(token);
//		mockMvc.perform(MockMvcRequestBuilders.post("/find").header("Authorization", "Bearer " + token)
//				.accept(MediaType.APPLICATION_JSON)).andExpect(status().isMethodNotAllowed());
//	}

	// without token cannot get the details
	@Test
	public void getOneEmployees1() throws JsonProcessingException, Exception {
		System.err.println(token);
		mockMvc.perform(MockMvcRequestBuilders.post("/find").accept(MediaType.APPLICATION_JSON))
				.andExpect(status().is4xxClientError());

	}

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Authentication-MS/src/test/java/com/cognizant/authenticationservice/Tests.java:Tests.<init>
// Node: setUp
// Node: webAppContextSetup
// Node: parseResponse
// Node: getResponse
// Node: getContentAsString
// Node: readValue
// Node: saveEmployee
// Node: isCreated
// Node: jsonPath
// Node: exists
// Node: saveEmployeeNeg
// Node: doesNotExist
// Node: is2xxSuccessful
// Node: andReturn
// Node: login2
// Node: getOneEmployees
// Node: isMethodNotAllowed
// Node: getOneEmployees1
// Node: is4xxClientError
package com.cognizant.authenticationservice;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.io.UnsupportedEncodingException;
import java.util.ArrayList;
import java.util.List;

import org.junit.Before;
import org.junit.jupiter.api.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.context.junit4.SpringRunner;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.context.WebApplicationContext;

import com.cognizant.authenticationservice.model.AppUser;
import com.cognizant.authenticationservice.service.JwtUtil;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonMappingException;
import com.fasterxml.jackson.databind.ObjectMapper;

@RunWith(SpringRunner.class)
@SpringBootTest
@AutoConfigureMockMvc
public class AuthTests {

	@Autowired
	private MockMvc mockMvc;

	@Autowired
	private WebApplicationContext wc;

	@MockBean
	private JwtUtil jwtUtil;

	public String token = "eytoken";
	List<AppUser> employees = new ArrayList<AppUser>();
	static ObjectMapper mapper = new ObjectMapper();

	@Before
	// before testing class login should be done
	// it execute before all methods
	public void setUp() throws JsonProcessingException, Exception {
		mockMvc = MockMvcBuilders.webAppContextSetup(wc).build();
		login();
	}

	public static <T> T parseResponse(MvcResult result, Class<T> responseClass)
			throws UnsupportedEncodingException, JsonMappingException, JsonProcessingException {

		String contentAsString = result.getResponse().getContentAsString();
		return mapper.readValue(contentAsString, responseClass);

	}

	// save employee mapping is tested
	@Test
	public void saveEmployee() throws JsonProcessingException, Exception {
		AppUser menu = new AppUser("111", "ba", "ba", "", "EMPLOYEE");
		String json = mapper.writeValueAsString(menu);
		mockMvc.perform(MockMvcRequestBuilders.post("/createUser").content(json).contentType(MediaType.APPLICATION_JSON)
				.accept(MediaType.APPLICATION_JSON)).andExpect(status().isCreated())
				.andExpect(MockMvcResultMatchers.jsonPath("$.userid").exists());
	}

	// save employee negative test case
	@Test
	public void saveEmployeeNeg() throws JsonProcessingException, Exception {
		AppUser menu = new AppUser("111", "yam", "yam", "", "EMPLOYEE");
		String json = mapper.writeValueAsString(menu);
		mockMvc.perform(MockMvcRequestBuilders.post("/createUser").content(json).contentType(MediaType.APPLICATION_JSON)
				.accept(MediaType.APPLICATION_JSON)).andExpect(status().is2xxSuccessful())
				.andExpect(MockMvcResultMatchers.jsonPath("$.userid1").doesNotExist());

	}

	// login method is tested

	@Test
	public void login() throws JsonProcessingException, Exception {
		AppUser menu = new AppUser("EMPLOYEE101", "emp", "emp", "eyToken", "EMPLOYEE");
		String json = mapper.writeValueAsString(menu);
		MvcResult andReturn = mockMvc.perform(MockMvcRequestBuilders.post("/login").content(json)
				.contentType(MediaType.APPLICATION_JSON).accept(MediaType.APPLICATION_JSON))
				.andExpect(status().is2xxSuccessful()).andReturn();
		AppUser response = parseResponse(andReturn, AppUser.class);
		token = response.getAuthToken();
	}

	// check if token is wrong the login should not proceed
	@Test
	public void login2() throws JsonProcessingException, Exception {
		AppUser menu = new AppUser("EMPLOYEE101", "emp", "emp", "", "EMPLOYEE");
		String json = mapper.writeValueAsString(menu);
		mockMvc.perform(MockMvcRequestBuilders.post("/login").content(json).contentType(MediaType.APPLICATION_JSON)
				.accept(MediaType.APPLICATION_JSON)).andExpect(status().is2xxSuccessful())
				.andExpect(MockMvcResultMatchers.jsonPath("$.authToken2").doesNotExist()).andReturn();
	}

//before find the method is checked here	
	@Test
	public void getOneEmployees() throws JsonProcessingException, Exception {
		System.err.println(token);
		mockMvc.perform(MockMvcRequestBuilders.post("/find").header("Authorization", "Bearer " + token)
				.accept(MediaType.APPLICATION_JSON)).andExpect(status().isMethodNotAllowed());
	}

	// without token cannot get the details
	@Test
	public void getOneEmployees1() throws JsonProcessingException, Exception {
		System.err.println(token);
		mockMvc.perform(MockMvcRequestBuilders.post("/find").accept(MediaType.APPLICATION_JSON))
				.andExpect(status().isMethodNotAllowed());

	}

	// check the health of microservice
	@Test
	public void geHealth() throws JsonProcessingException, Exception {
		System.err.println(token);
		MvcResult andReturn = mockMvc.perform(MockMvcRequestBuilders.get("/health").accept(MediaType.APPLICATION_JSON))
				.andExpect(status().isOk()).andReturn();

		boolean equals = andReturn.getResponse().getContentAsString().equals("UP");
		assertEquals(equals, true);

	}

	@Test
	public void geHealthNeg() throws JsonProcessingException, Exception {
		System.err.println(token);
		MvcResult andReturn = mockMvc.perform(MockMvcRequestBuilders.get("/health").accept(MediaType.APPLICATION_JSON))
				.andExpect(status().isOk()).andReturn();

		boolean equals = andReturn.getResponse().getContentAsString().equals("DOWN");
		assertNotEquals(equals, true);

	}

	@Test
	public void geValidate() throws JsonProcessingException, Exception {
		System.err.println(token);
		mockMvc.perform(MockMvcRequestBuilders.get("/validateToken").header("Authorization", "Bearer " + token)
				.accept(MediaType.APPLICATION_JSON)).andExpect(status().isOk());

	}

	@Test
	public void getNotValidate() throws JsonProcessingException, Exception {
		System.err.println(token);
		mockMvc.perform(MockMvcRequestBuilders.get("/validateToken").header("Authorization", token)
				.accept(MediaType.APPLICATION_JSON)).andExpect(status().isOk()).andReturn();

	}

//	
	@Test
	public void setterNameTest() throws NoSuchFieldException, IllegalAccessException {
		// given
		AppUser pojo = new AppUser();
		// when
		pojo.setUsername("nagarjun");
		// then
		java.lang.reflect.Field field = pojo.getClass().getDeclaredField("username");
		field.setAccessible(true);
		assertEquals("nagarjun", field.get(pojo));
	}

	@Test
	public void setterNameTestNeg() throws NoSuchFieldException, IllegalAccessException {
		// given
		AppUser pojo = new AppUser();
		// when
		pojo.setUsername("abcd");
		// then
		java.lang.reflect.Field field = pojo.getClass().getDeclaredField("username");
		field.setAccessible(true);
		assertNotEquals("Fields didn't match", field.get(pojo), "abc");
	}

//	
	@Test
	public void getterNameTest() throws NoSuchFieldException, IllegalAccessException {
		// given
		AppUser pojo = new AppUser();
		java.lang.reflect.Field field = pojo.getClass().getDeclaredField("username");
		field.setAccessible(true);
		field.set(pojo, "magic_values");
		// when
		String result = pojo.getUsername();
		// then
		assertEquals("magic_values", result);
	}

	@Test
	public void getterNameTestNeg() throws NoSuchFieldException, IllegalAccessException {
		// given
		AppUser pojo = new AppUser();
		java.lang.reflect.Field field = pojo.getClass().getDeclaredField("username");
		field.setAccessible(true);
		field.set(pojo, "values");
		// when
		String result = pojo.getUsername();
		// then
		assertNotEquals("field wasn't retrieved properly", result, "magic_values");
	}

	@Test
	public void setterPassTest() throws NoSuchFieldException, IllegalAccessException {
		// given
		AppUser pojo = new AppUser();
		// when
		pojo.setPassword("nagarjun");
		// then
		java.lang.reflect.Field field = pojo.getClass().getDeclaredField("password");
		field.setAccessible(true);
		assertEquals("nagarjun", field.get(pojo));
	}

	@Test
	public void setterPassTestNeg() throws NoSuchFieldException, IllegalAccessException {
		// given
		AppUser pojo = new AppUser();
		// when
		pojo.setPassword("abcde");
		// then
		java.lang.reflect.Field field = pojo.getClass().getDeclaredField("password");
		field.setAccessible(true);
		assertNotEquals("Fields didn't match", field.get(pojo), "abc");
	}

	@Test
	public void getRoleTest() throws Exception {
		mockMvc.perform(MockMvcRequestBuilders.get("/role").accept(MediaType.APPLICATION_JSON)).andReturn();
	}

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Authentication-MS/src/test/java/com/cognizant/authenticationservice/AuthTests.java:AuthTests.<init>
// Node: geHealth
// Node: geHealthNeg
// Node: assertNotEquals
// Node: geValidate
// Node: getNotValidate
// Node: setterNameTest
// Node: getClass
// Node: getDeclaredField
// Node: setAccessible
// Node: setterNameTestNeg
// Node: getterNameTest
// Node: set
// Node: getterNameTestNeg
// Node: setterPassTest
// Node: setterPassTestNeg
package com.cognizant.authenticationservice.model;

import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class AppUserTest {

	AppUser app = new AppUser("1", "naga", "abc", "a", "user");
	AppUser pojo = new AppUser();

	//

	@Test
	public void getterPassTestNeg() throws NoSuchFieldException, IllegalAccessException {
		// given
		AppUser pojo = new AppUser();
		java.lang.reflect.Field field = pojo.getClass().getDeclaredField("password");
		field.setAccessible(true);
		field.set(pojo, "magic_value");
		// when
		String result = pojo.getPassword();
		// then
		assertNotEquals("field wasn't retrieved properly", result, "magic_values");
	}

	@Test
	public void setterIdTestNeg() throws NoSuchFieldException, IllegalAccessException {
		// given
		AppUser pojo = new AppUser();
		// when
		pojo.setUserid("abcd");
		// then
		java.lang.reflect.Field field = pojo.getClass().getDeclaredField("userid");
		field.setAccessible(true);
		assertNotEquals("Fields didn't match", field.get(pojo), "emp");
	}

	@Test
	public void getterIdNeg() throws NoSuchFieldException, IllegalAccessException {
		// given
		AppUser pojo = new AppUser();
		java.lang.reflect.Field field = pojo.getClass().getDeclaredField("userid");
		field.setAccessible(true);
		field.set(pojo, "values");
		// when
		String result = pojo.getUserid();
		// then
		assertNotEquals("field wasn't retrieved properly", result, "magic_values");
	}

	@Test
	void setAmountTest() {
		pojo.setAuthToken("abc");
		assertEquals("abc", pojo.getAuthToken());
	}

	@Test
	void getAccountIdTest() {
		pojo.setAuthToken("abc");
		assertTrue(pojo.getAuthToken() == "abc");
	}

	@Test
	void set() {
		pojo.setRole("abc");
		assertEquals("abc", pojo.getRole());
	}

	@Test
	void getAccounTest() {
		pojo.setRole("abc");
		assertTrue(pojo.getRole() == "abc");
	}

	@Test
	void setname() {
		pojo.setUsername("abc");
		assertEquals("abc", pojo.getUsername());
	}

	@Test
	void getAccounname() {
		pojo.setUsername("abc");
		assertTrue(pojo.getUsername() == "abc");
	}

	AuthenticationResponse response = new AuthenticationResponse();
	AuthenticationResponse response2 = new AuthenticationResponse();
	AuthenticationResponse response3 = new AuthenticationResponse("1", "name", true);

	@Test
	void setUserIdTest() {
		response.setUserid("Cust101");
		assertEquals("Cust101", response.getUserid());
	}

	@Test
	void getUserIdTest() {
		response.setUserid("Cust101");
		assertTrue(response.getUserid() == "Cust101");
	}

	@Test
	void setNameTest() {
		response.setName("Pratik B");
		assertEquals("Pratik B", response.getName());
	}

	@Test
	void getNameTest() {
		response.setName("Cust101");
		assertTrue(response.getName() == "Cust101");
	}

	@Test
	void setisValidTest() {
		response.setValid(true);
		assertEquals(true, response.isValid());
	}

	@Test
	void toSringTest() {
		assertEquals(response2.toString(), response.toString());
	}

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Authentication-MS/src/test/java/com/cognizant/authenticationservice/model/AppUserTest.java:AppUserTest.<init>
// Node: getterPassTestNeg
// Node: setterIdTestNeg
// Node: getterIdNeg
package com.rulesservice.controller;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.timeout;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.util.ArrayList;
import java.util.List;

import org.junit.jupiter.api.Test;
import org.junit.runner.RunWith;
import org.mockito.Mock;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.ImportAutoConfiguration;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.cloud.netflix.ribbon.RibbonAutoConfiguration;
import org.springframework.cloud.openfeign.FeignAutoConfiguration;
import org.springframework.cloud.openfeign.ribbon.FeignRibbonClientAutoConfiguration;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.test.context.junit4.SpringRunner;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.rulesservice.exception.MinimumBalanceException;
import com.rulesservice.feign.AccountFeign;
import com.rulesservice.feign.AuthorizationFeign;
import com.rulesservice.model.RulesInput;
import com.rulesservice.model.Account;
import com.rulesservice.model.AuthenticationResponse;
import com.rulesservice.model.ServiceResponse;
import com.rulesservice.service.RulesServiceImpl;

@RunWith(SpringRunner.class)
@WebMvcTest(controllers = RulesController.class)
@ImportAutoConfiguration({ RibbonAutoConfiguration.class, FeignRibbonClientAutoConfiguration.class,
		FeignAutoConfiguration.class })
class RulesControllerTest {

	@Autowired
	MockMvc mockMvc;

	@MockBean
	AuthorizationFeign authProxy;

	@MockBean
	RulesServiceImpl rulesService;

	@Mock
	AccountFeign accountFeign;

	@Test
	void evaluateTest() throws Exception {
		when(rulesService.hasPermission("token")).thenReturn(new AuthenticationResponse("Employee101", "emp", true));
		RulesInput inp = new RulesInput(101, 1200, 100);
		when(rulesService.evaluate(inp)).thenReturn(true);
		mockMvc.perform(MockMvcRequestBuilders.post("/evaluateMinBal").content(asJsonString(inp))
				.contentType(MediaType.APPLICATION_JSON).accept(MediaType.APPLICATION_JSON)
				.header("Authorization", "token")).andExpect(status().isOk());

	}

	@Test
	void evaluateTestEqual() throws Exception {
		when(rulesService.hasPermission("token")).thenReturn(new AuthenticationResponse("Employee101", "emp", true));
		RulesInput inp = new RulesInput(101, 100, 100);
		when(rulesService.evaluate(inp)).thenReturn(true);
		mockMvc.perform(MockMvcRequestBuilders.post("/evaluateMinBal").content(asJsonString(inp))
				.contentType(MediaType.APPLICATION_JSON).accept(MediaType.APPLICATION_JSON)
				.header("Authorization", "token")).andExpect(status().isOk());

	}

	@Test
	void evaluateTestNeg() throws Exception {
		when(rulesService.hasPermission("token")).thenReturn(new AuthenticationResponse("Employee101", "emp", true));
		RulesInput inp = new RulesInput(101, 200, 100);
		when(rulesService.evaluate(inp)).thenReturn(false);
		mockMvc.perform(MockMvcRequestBuilders.post("/evaluateMinBal").content(asJsonString(inp))
				.contentType(MediaType.APPLICATION_JSON).accept(MediaType.APPLICATION_JSON)
				.header("Authorization", "token")).andExpect(status().isOk());

	}

	@Test
	void serviceChargesTestNegative() throws Exception {
		when(rulesService.hasPermission("token")).thenReturn(new AuthenticationResponse("Employee101", "emp", true));
		when(accountFeign.getAllacc("token"))
				.thenReturn(new ResponseEntity<List<Account>>(new ArrayList<>(), HttpStatus.OK));
		mockMvc.perform(MockMvcRequestBuilders.post("/serviceCharges").header("Authorization", "token"))
				.andExpect(status().is(500));
		verify(rulesService, timeout(1)).hasPermission("token");

	}

	@Test
	public void MinimumBal() throws MinimumBalanceException, Exception {
		RulesController con = new RulesController();
		RulesInput account = new RulesInput(0, 0, 0);
		Throwable exception = assertThrows(MinimumBalanceException.class, () -> con.evaluate(account));
		assertEquals("Send Valid Details.", exception.getMessage());

	}

	public static String asJsonString(final Object obj) throws JsonProcessingException {

		final ObjectMapper mapper = new ObjectMapper();
		final String jsonContent = mapper.writeValueAsString(obj);
		return jsonContent;

	}

}

// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Rules-MS/src/test/java/com/rulesservice/controller/RulesControllerTest.java:RulesControllerTest.<init>
// Node: WebMvcTest
// Node: ImportAutoConfiguration
// Node: evaluateTest
// Node: evaluateTestEqual
// Node: evaluateTestNeg
// Node: serviceChargesTestNegative
// Node: is
// Node: MinimumBal
// Node: RulesController
package com.rulesservice.model;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

class AppUserTest {

	AppUser accInp = new AppUser();
	AppUser accInp2 = new AppUser("2","bhavya","bhavya","xyz","user");

	@Test
	void setAccountIdTest() {
		accInp.setUsername("bhavya");
		assertEquals("bhavya", accInp.getUsername());
	}

	@Test
	void setAmountTest() {
		accInp.setUserid("emp");
		assertEquals("emp", accInp.getUserid());
	}

	@Test
	public void setPasswoedTest() {
		accInp.setPassword("abc");
		assertEquals("abc", accInp.getPassword());
	}

	@Test
	public void setAuthTokenTest() {
		accInp.setAuthToken("token");
		assertEquals("token", accInp.getAuthToken());
	}

	@Test
	public void setRoleTest() {
		accInp.setRole("user");
		assertEquals("user", accInp.getRole());
	}
	
	@Test
	void getAccIdTest1() {
		assertEquals("2", accInp2.getUserid());
	}

	@Test
	void getRoleTest1() {
		assertEquals("user", accInp2.getRole());
	}

	@Test
	void getUsernameTest1() {
		assertEquals("bhavya", accInp2.getUsername());
	}

	@Test
	void getPasswordTest1() {
		assertEquals("bhavya", accInp2.getPassword());
	}

	@Test
	void getTokenTest1() {
		assertEquals("xyz", accInp2.getAuthToken());
	}
}

// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Rules-MS/src/test/java/com/rulesservice/model/AppUserTest.java:AppUserTest.<init>
package com.cognizant.CustomerServiceTest.model;

import static org.junit.Assert.*;
import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

import com.cognizant.customerservice.model.AppUser;


class AppUserTest {
	AppUser accInp = new AppUser();
	AppUser accInp2 = new AppUser("2","prabha","prabha","xyz","user");

	@Test
	void setAccountIdTest() {
		accInp.setUserid("1");
		assertEquals("1", accInp.getUserid());
	}

	@Test
	void setRoleTest() {
		accInp.setRole("user");
		assertEquals("user", accInp.getRole());
	}

	@Test
	void setUsernameTest() {
		accInp.setUsername("1");
		assertEquals("1", accInp.getUsername());
	}

	@Test
	void setPassTest() {
		accInp.setPassword("user");
		assertEquals("user", accInp.getPassword());
	}

	@Test
	void setAuthTokenTest() {
		accInp.setAuthToken("user");
		assertEquals("user", accInp.getAuthToken());
	}

	@Test
	void getAccIdTest() {
		accInp.setUserid("1");
		assertEquals("1", accInp.getUserid());
	}

	@Test
	void getRoleTest() {
		accInp.setRole("user");
		assertEquals("user", accInp.getRole());
	}

	@Test
	void getUsernameTest() {
		accInp.setUsername("1");
		assertEquals("1", accInp.getUsername());
	}

	@Test
	void getPasswordTest() {
		accInp.setPassword("user");
		assertEquals("user", accInp.getPassword());
	}

	@Test
	void getTokenTest() {
		accInp.setAuthToken("token");
		assertEquals("token", accInp.getAuthToken());
	}

	@Test
	void getAccIdTest1() {
		assertEquals("2", accInp2.getUserid());
	}

	@Test
	void getRoleTest1() {
		assertEquals("user", accInp2.getRole());
	}

	@Test
	void getUsernameTest1() {
		assertEquals("prabha", accInp2.getUsername());
	}

	@Test
	void getPasswordTest1() {
		assertEquals("prabha", accInp2.getPassword());
	}

	@Test
	void getTokenTest1() {
		assertEquals("xyz", accInp2.getAuthToken());
	}
	
	

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Customer-MS/src/test/java/com/cognizant/CustomerServiceTest/model/AppUserTest.java:AppUserTest.<init>
package com.cognizant.CustomerServiceTest.model;

import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.Test;

import com.cognizant.customerservice.model.AccountCreationStatus;


class AccountStatusTest {
	AccountCreationStatus account = new AccountCreationStatus();
	AccountCreationStatus account2 = new AccountCreationStatus(111,"hi");
	

	@Test
	void setAccTest() {
		account.setAccountId(1);
		assertEquals(1, account.getAccountId());
	}

	@Test
	void setMsgTest() {
		account.setMessage("msg");
		assertEquals("msg", account.getMessage());
	}

	@Test
	void getMessageTest() {
		account.setMessage("msg");
		assertEquals("msg", account.getMessage());
	}

	@Test
	void getAccTest() {
		account.setAccountId(1);
		assertEquals(1, account.getAccountId());
	}

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Customer-MS/src/test/java/com/cognizant/CustomerServiceTest/model/AccountStatusTest.java:AccountStatusTest.<init>
package com.cognizant.CustomerService.controller;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.Assert.assertEquals;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.sql.Date;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.junit4.SpringJUnit4ClassRunner;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.context.WebApplicationContext;

import com.cognizant.customerservice.model.AuthenticationResponse;
import com.cognizant.customerservice.CustomerServiceApplication;
import com.cognizant.customerservice.model.AppUser;
import com.cognizant.customerservice.model.CustomerEntity;
import com.cognizant.customerservice.service.CustomerService;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

import springfox.documentation.service.ApiInfo;
import springfox.documentation.service.Contact;

@SpringBootTest
@RunWith(SpringJUnit4ClassRunner.class)
@ContextConfiguration(classes = { CustomerServiceApplication.class })
public class CustomerTests {

	public String token = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJFTVBMT1lFRTEwMSIsImV4cCI6MTYwODU3MDk1MSwiaWF0IjoxNjA4MzU0OTUxfQ.CLuewsfeFIYwVIGftqkMGhvuEf4PqP4Fl8TKKIifNtw";

	private MockMvc mockMvc;

	@Autowired
	private WebApplicationContext wc;
	@MockBean
	private CustomerService customerService;

	List<AppUser> employees = new ArrayList<AppUser>();
	static ObjectMapper MAPPER = new ObjectMapper();

	@Before
	public void setUp() throws JsonProcessingException, Exception {
		mockMvc = MockMvcBuilders.webAppContextSetup(wc).build();
	}

	@Test
	public void createCustomer() throws JsonProcessingException, Exception {
		System.err.println(token);
		CustomerEntity ce = null;
		String json = MAPPER.writeValueAsString(ce);
		@SuppressWarnings("unused")
		MvcResult andReturn = mockMvc
				.perform(MockMvcRequestBuilders.post("/createCustomer").header("Authorization", "Bearer " + token)
						.content(json).contentType(MediaType.APPLICATION_JSON).accept(MediaType.APPLICATION_JSON))
				.andExpect(status().is(400)).andReturn();

	}

	@Test
	public void saveCustomerNull() throws JsonProcessingException, Exception {
		System.err.println(token);
		CustomerEntity ce = null;
		String json = MAPPER.writeValueAsString(ce);
		@SuppressWarnings("unused")
		MvcResult andReturn = mockMvc
				.perform(MockMvcRequestBuilders.post("/saveCustomer").header("Authorization", "Bearer " + token)
						.content(json).contentType(MediaType.APPLICATION_JSON).accept(MediaType.APPLICATION_JSON))
				.andExpect(status().is(400)).andReturn();

	}

	@Test
	public void saveCustomers() throws JsonProcessingException, Exception {
		System.err.println(token);
		CustomerEntity ce = new CustomerEntity();
		ce.setAddress("Hyderabad");
		ce.setDateOfBirth(new Date(60));
		ce.setPan("ABCDE1234R");
		ce.setPassword("prabha");
		ce.setUsername("prabha");
		ce.setUserid("1234");
		String json = MAPPER.writeValueAsString(ce);
		@SuppressWarnings("unused")
		MvcResult andReturn = mockMvc
				.perform(MockMvcRequestBuilders.post("/saveCustomer").header("Authorization", "Bearer " + token)
						.content(json).contentType(MediaType.APPLICATION_JSON).accept(MediaType.APPLICATION_JSON))
				.andExpect(status().is(200)).andReturn();

	}

	@Test
	public void saveCustomers2() throws JsonProcessingException, Exception {
		System.err.println(token);
		CustomerEntity ce = new CustomerEntity();
		ce.setAddress("Hyderabad");
		ce.setDateOfBirth(new Date(60));
		ce.setPan("ABCFE1234R");
		ce.setPassword("prabha");
		ce.setUsername("prabha");
		ce.setUserid("12345");
		String json = MAPPER.writeValueAsString(ce);
		@SuppressWarnings("unused")
		MvcResult andReturn = mockMvc
				.perform(MockMvcRequestBuilders.post("/saveCustomer").header("Authorization", "Bearer " + token)
						.content(json).contentType(MediaType.APPLICATION_JSON).accept(MediaType.APPLICATION_JSON))
				.andExpect(status().is(200)).andReturn();

	}

	@Test
	public void updateCustomers() throws JsonProcessingException, Exception {
		System.err.println(token);
		CustomerEntity ce = new CustomerEntity();
		ce.setAddress("Hyderabad");
		ce.setDateOfBirth(new Date(60));
		ce.setPan("ABCDE1234R");
		ce.setPassword("prabha");
		ce.setUsername("prabha");
		ce.setUserid("CUSTOMER101");
		String json = MAPPER.writeValueAsString(ce);
		when(customerService.hasEmployeePermission("token"))
				.thenReturn(new AuthenticationResponse("CUSTOMER101", "cust", true));
		@SuppressWarnings("unused")
		MvcResult andReturn = mockMvc
				.perform(MockMvcRequestBuilders.post("/updateCustomer").header("Authorization", "Bearer " + token)
						.content(json).contentType(MediaType.APPLICATION_JSON).accept(MediaType.APPLICATION_JSON))
				.andExpect(status().is(200)).andReturn();

	}

	@Test
	public void getCustomersSuccess() throws JsonProcessingException, Exception {
		System.err.println(token);
		CustomerEntity ce = new CustomerEntity();
		ce.setAddress("Hyderabad");
		ce.setDateOfBirth(new Date(60));
		ce.setPan("ABCFE1234R");
		ce.setPassword("prabha");
		ce.setUsername("prabha");
		ce.setUserid("CUSTOMER101");
		when(customerService.hasPermission("token"))
				.thenReturn(new AuthenticationResponse("CUSTOMER101", "cust", true));
		when(customerService.getCustomerDetail("token", "CUSTOMER101")).thenReturn(ce);
		mockMvc.perform(get("/getCustomerDetails/CUSTOMER101").header("Authorization", "token"))
				.andExpect(status().isOk());
	}

	@Test
	public void getCustomersfail() throws JsonProcessingException, Exception {
		System.err.println(token);
		CustomerEntity ce = new CustomerEntity();
		ce.setAddress("Hyderabad");
		ce.setDateOfBirth(new Date(60));
		ce.setPan("ABCFE1234R");
		ce.setPassword("prabha");
		ce.setUsername("prabha");
		ce.setUserid("CUSTOMER101");
		when(customerService.hasEmployeePermission(token))
				.thenReturn(new AuthenticationResponse("CUSTOMER101", "cust", true));
		when(customerService.getCustomerDetail(token, "CUSTOMER101")).thenReturn(ce);
		mockMvc.perform(MockMvcRequestBuilders.get("/getCustomerDetails/CUSTOMER101").header("Authorization",
				"Bearer " + token)).andExpect(status().is(406));

	}

	@Test
	public void unsuccesfulCustomer() throws JsonProcessingException, Exception {
		System.err.println(token);
		CustomerEntity ce = new CustomerEntity();
		ce.setAddress("Hyderabad");
		ce.setDateOfBirth(new Date(60));
		ce.setPan("ABCDE1234R");
		ce.setPassword("prabha");
		ce.setUsername("prabha");
		ce.setUserid("1234");
		String json = MAPPER.writeValueAsString(ce);
		mockMvc.perform(MockMvcRequestBuilders.post("/createCustomer").header("Authorization", "Bearer " + token)
				.content(json).contentType(MediaType.APPLICATION_JSON).accept(MediaType.APPLICATION_JSON))
				.andExpect(status().is(406)).andReturn();
	}

	@Test
	public void withoutValidate() throws Exception {
		MvcResult andReturn = mockMvc.perform(MockMvcRequestBuilders.get("/check")
				.header("Authorization", "Bearer " + token).accept(MediaType.APPLICATION_JSON))
				.andExpect(status().isOk()).andReturn();
		String contentAsString = andReturn.getResponse().getContentAsString();
		assertEquals("Your Token is valid", contentAsString);
	}

	@Test
	public void deleteNotPresentEmployeeAPI() throws Exception {
		mockMvc.perform(MockMvcRequestBuilders.delete("/deleteCustomer/CUSTOMER101", 1).header("Authorization",
				"Bearer " + token)).andExpect(status().is(406));
	}


	@Test
	public void AppInfoCheck() {
		ApiInfo a1 = new ApiInfo("Customer Service", "Retail Banking Project", "API", "Terms of service",
				new Contact("ABC", "", "abc@email.com"), "License of API", "", Collections.emptyList());
		ApiInfo a2 = new ApiInfo("Customer Service", "Retail Banking Project", "API", "Terms of service",
				new Contact("ABC", "", "abc@email.com"), "License of API", "", Collections.emptyList());
		assertThat(a1).isNotEqualTo(a2);
	}

}

// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Customer-MS/src/test/java/com/cognizant/CustomerService/controller/CustomerTests.java:CustomerTests.<init>
// Node: ContextConfiguration
// Node: saveCustomerNull
// Node: saveCustomers
// Node: saveCustomers2
// Node: updateCustomers
// Node: getCustomersSuccess
// Node: getCustomersfail
// Node: unsuccesfulCustomer
// Node: withoutValidate
// Node: deleteNotPresentEmployeeAPI
// Node: delete
// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Authentication-MS/bin/src/main/java/com/retailbank/AuthenticationMS/Repository/UserRepository.class:UserRepository
// Node: String
// Node: Repository
