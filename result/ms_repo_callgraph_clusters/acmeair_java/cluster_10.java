// Cluster 10

package com.acmeair.web;

import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;

import javax.ws.rs.core.Application;
import javax.ws.rs.ApplicationPath;

import com.acmeair.config.AcmeAirConfiguration;
import com.acmeair.config.LoaderREST;

@ApplicationPath("/rest/info")
public class AppConfig extends Application {
    public Set<Class<?>> getClasses() {
        return new HashSet<Class<?>>(Arrays.asList(LoaderREST.class, AcmeAirConfiguration.class));
    }
}


// Node: repos/cloned_ms_repos/acmeair/acmeair-webapp/src/main/java/com/acmeair/web/AppConfig.java:AppConfig.<init>
// Node: ApplicationPath
// Node: getClasses
// Node: asList
package com.acmeair.web;

import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;

import javax.ws.rs.core.Application;
import javax.ws.rs.ApplicationPath;

@ApplicationPath("/rest/api")
public class AcmeAirApp extends Application {
    public Set<Class<?>> getClasses() {
        return new HashSet<Class<?>>(Arrays.asList(BookingsREST.class, CustomerREST.class, FlightsREST.class, LoginREST.class));
    }
}


// Node: repos/cloned_ms_repos/acmeair/acmeair-webapp/src/main/java/com/acmeair/web/AcmeAirApp.java:AcmeAirApp.<init>
