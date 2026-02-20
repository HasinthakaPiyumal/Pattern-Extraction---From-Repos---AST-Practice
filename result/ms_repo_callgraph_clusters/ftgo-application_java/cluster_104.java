// Cluster 104

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


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-restaurant-service-aws-lambda/src/main/java/net/chrisrichardson/ftgo/restaurantservice/lambda/AbstractAutowiringHttpRequestHandler.java:AbstractAutowiringHttpRequestHandler.<init>
// Node: ReentrantReadWriteLock
