// Cluster 56

/**
 * (C) Copyright IBM Corporation 2016.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims;

/**
 * Simple bean to get and set messages
 */

public class PingBean {

    private String msg;

    /**
     * returns the message contained in the bean
     *
     * @return message String
     **/
    public String getMsg() {
        return msg;
    }

    /**
     * sets the message contained in the bean param message String
     **/
    public void setMsg(String s) {
        msg = s;
    }
}

// Node: getMsg
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims;

import javax.ejb.Local;
import javax.ejb.Stateful;

/**
 *
 */
@Stateful
@Local
public class PingEJBLocal implements PingEJBIFace {

    private static int hitCount;

    /*
     * (non-Javadoc)
     * 
     * @see com.ibm.websphere.samples.daytrader.web.prims.EJBIFace#getMsg()
     */
    @Override
    public String getMsg() {

        return "PingEJBLocal: " + hitCount++;
    }

}


// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/PingEJBLocal.java:PingEJBLocal.<init>
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims;

import javax.annotation.Priority;
import javax.decorator.Decorator;
import javax.decorator.Delegate;
import javax.inject.Inject;
import javax.interceptor.Interceptor;

@Decorator
@Priority(Interceptor.Priority.APPLICATION)
public class PingEJBLocalDecorator implements PingEJBIFace {

    /*
     * (non-Javadoc)
     * 
     * @see com.ibm.websphere.samples.daytrader.web.prims.EJBIFace#getMsg()
     */
    @Delegate
    @Inject
    PingEJBIFace ejb;

    @Override
    public String getMsg() {

        return "Decorated " + ejb.getMsg();
    }

}


// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/PingEJBLocalDecorator.java:PingEJBLocalDecorator.<init>
// Node: Priority
/**
 * (C) Copyright IBM Corporation 2016.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims;

/**
 * EJB interface
 */
public interface PingEJBIFace {

    public String getMsg();
}


// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/PingEJBIFace.java:PingEJBIFace.<init>
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims;

import java.io.Serializable;

import javax.annotation.Priority;
import javax.interceptor.AroundInvoke;
import javax.interceptor.Interceptor;
import javax.interceptor.InvocationContext;

/**
 *
 */
@PingInterceptorBinding
@Interceptor
@Priority(Interceptor.Priority.APPLICATION)
public class PingInterceptor implements Serializable {

    /**  */
    private static final long serialVersionUID = 1L;

    @AroundInvoke
    public Object methodInterceptor(InvocationContext ctx) throws Exception {

        //noop
        return ctx.proceed();
    }
}


// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/PingInterceptor.java:PingInterceptor.<init>
// Node: methodInterceptor
// Node: proceed
