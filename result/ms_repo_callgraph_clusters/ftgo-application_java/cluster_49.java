// Cluster 49

package net.chrisrichardson.ftgo.restaurantservice.aws;

public class RequestContext {

  private String accountId;
  private String resourceId;
  private String stage;
  private String requestId;
  private Identity identity;
  private String resourcePath;
  private String httpMethod;
  private String apiId;

  public String getAccountId() {
    return accountId;
  }

  public void setAccountId(String accountId) {
    this.accountId = accountId;
  }

  public String getResourceId() {
    return resourceId;
  }

  public void setResourceId(String resourceId) {
    this.resourceId = resourceId;
  }

  public String getStage() {
    return stage;
  }

  public void setStage(String stage) {
    this.stage = stage;
  }

  public String getRequestId() {
    return requestId;
  }

  public void setRequestId(String requestId) {
    this.requestId = requestId;
  }

  public Identity getIdentity() {
    return identity;
  }

  public void setIdentity(Identity identity) {
    this.identity = identity;
  }

  public String getResourcePath() {
    return resourcePath;
  }

  public void setResourcePath(String resourcePath) {
    this.resourcePath = resourcePath;
  }

  public String getHttpMethod() {
    return httpMethod;
  }

  public void setHttpMethod(String httpMethod) {
    this.httpMethod = httpMethod;
  }

  public String getApiId() {
    return apiId;
  }

  public void setApiId(String apiId) {
    this.apiId = apiId;
  }

}

// Node: setAccountId
package net.chrisrichardson.ftgo.restaurantservice.aws;

public class Identity {

  private String cognitoIdentityPoolId;
  private String accountId;
  private String cognitoIdentityId;
  private String caller;
  private String apiKey;
  private String sourceIp;
  private String cognitoAuthenticationType;
  private String cognitoAuthenticationProvider;
  private String userArn;
  private String userAgent;
  private String user;

  public String getCognitoIdentityPoolId() {
    return cognitoIdentityPoolId;
  }

  public void setCognitoIdentityPoolId(String cognitoIdentityPoolId) {
    this.cognitoIdentityPoolId = cognitoIdentityPoolId;
  }

  public String getAccountId() {
    return accountId;
  }

  public void setAccountId(String accountId) {
    this.accountId = accountId;
  }

  public String getCognitoIdentityId() {
    return cognitoIdentityId;
  }

  public void setCognitoIdentityId(String cognitoIdentityId) {
    this.cognitoIdentityId = cognitoIdentityId;
  }

  public String getCaller() {
    return caller;
  }

  public void setCaller(String caller) {
    this.caller = caller;
  }

  public String getApiKey() {
    return apiKey;
  }

  public void setApiKey(String apiKey) {
    this.apiKey = apiKey;
  }

  public String getSourceIp() {
    return sourceIp;
  }

  public void setSourceIp(String sourceIp) {
    this.sourceIp = sourceIp;
  }

  public String getCognitoAuthenticationType() {
    return cognitoAuthenticationType;
  }

  public void setCognitoAuthenticationType(String cognitoAuthenticationType) {
    this.cognitoAuthenticationType = cognitoAuthenticationType;
  }

  public String getCognitoAuthenticationProvider() {
    return cognitoAuthenticationProvider;
  }

  public void setCognitoAuthenticationProvider(String cognitoAuthenticationProvider) {
    this.cognitoAuthenticationProvider = cognitoAuthenticationProvider;
  }

  public String getUserArn() {
    return userArn;
  }

  public void setUserArn(String userArn) {
    this.userArn = userArn;
  }

  public String getUserAgent() {
    return userAgent;
  }

  public void setUserAgent(String userAgent) {
    this.userAgent = userAgent;
  }

  public String getUser() {
    return user;
  }

  public void setUser(String user) {
    this.user = user;
  }
}


package net.chrisrichardson.ftgo.accountingservice.web;

import io.eventuate.EntityNotFoundException;
import io.eventuate.sync.AggregateRepository;
import net.chrisrichardson.ftgo.accountingservice.domain.Account;
import net.chrisrichardson.ftgo.accountingservice.domain.AccountCommand;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping(path="/accounts")
public class AccountsController {

  @Autowired
  private AggregateRepository<Account, AccountCommand> accountRepository;

  @RequestMapping(path="/{accountId}", method= RequestMethod.GET)
  public ResponseEntity<GetAccountResponse> getAccount(@PathVariable String accountId) {
       try {
          return new ResponseEntity<>(new GetAccountResponse(accountId), HttpStatus.OK);
       } catch (EntityNotFoundException e) {
         return  new ResponseEntity<>(HttpStatus.NOT_FOUND);
       }
  }

}


// Node: getAccount
// Node: GetAccountResponse
package net.chrisrichardson.ftgo.accountingservice.web;

public class GetAccountResponse {
  private String accountId;

  public String getAccountId() {
    return accountId;
  }

  public void setAccountId(String accountId) {
    this.accountId = accountId;
  }

  public GetAccountResponse() {

  }

  public GetAccountResponse(String accountId) {
    this.accountId = accountId;
  }
}


