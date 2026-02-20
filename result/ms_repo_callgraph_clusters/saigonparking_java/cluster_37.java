// Cluster 37

package com.bht.saigonparking.common.loadbalance;

import java.net.URI;

import org.springframework.cloud.client.discovery.DiscoveryClient;

import io.grpc.NameResolver;
import io.grpc.NameResolverProvider;
import lombok.AllArgsConstructor;

/**
 * @author bht
 */
@AllArgsConstructor
public final class SaigonParkingNameResolverProvider extends NameResolverProvider {

    private final String serviceId;
    private final DiscoveryClient discoveryClient;

    @Override
    protected boolean isAvailable() {
        return true;
    }

    @Override
    protected int priority() {
        return 5;
    }

    @Override
    public String getDefaultScheme() {
        return "consul";
    }

    @Override
    public NameResolver newNameResolver(URI targetUri, NameResolver.Args args) {
        return new SaigonParkingNameResolver(discoveryClient, targetUri, serviceId);
    }
}

// Node: newNameResolver
// Node: SaigonParkingNameResolver
package com.bht.saigonparking.common.loadbalance;

import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.URI;
import java.util.ArrayList;
import java.util.List;

import org.apache.logging.log4j.Level;
import org.springframework.cloud.client.ServiceInstance;
import org.springframework.cloud.client.discovery.DiscoveryClient;

import com.bht.saigonparking.common.util.LoggingUtil;

import io.grpc.Attributes;
import io.grpc.EquivalentAddressGroup;
import io.grpc.NameResolver;
import lombok.Getter;

/**
 *
 * @author bht
 */
@Getter
public final class SaigonParkingNameResolver extends NameResolver {

    private final URI consulURI;
    private final String serviceId;
    private final DiscoveryClient discoveryClient;

    private Listener listener;
    private List<ServiceInstance> serviceInstances;

    public SaigonParkingNameResolver(DiscoveryClient discoveryClient,
                                     URI consulURI,
                                     String serviceId) {
        this.consulURI = consulURI;
        this.serviceId = serviceId;
        this.discoveryClient = discoveryClient;
    }

    @Override
    public String getServiceAuthority() {
        return consulURI.getAuthority();
    }

    @Override
    public void start(Listener2 listener) {
        this.listener = listener;
        loadServiceInstances();
    }

    @Override
    public void shutdown() {
        // implement shutdown...
    }

    private void loadServiceInstances() {

        List<EquivalentAddressGroup> addressList = new ArrayList<>();
        serviceInstances = discoveryClient.getInstances(serviceId);

        if (serviceInstances == null || serviceInstances.isEmpty()) {
            LoggingUtil.log(Level.WARN, "loadServiceInstances", "Warning",
                    String.format("no serviceInstances of %s", serviceId));
            return;
        }

        serviceInstances.forEach(serviceInstance -> {
            String host = serviceInstance.getHost();
            int port = serviceInstance.getPort();

            LoggingUtil.log(Level.INFO, "loadServiceInstances", serviceId, String.format("%s:%d", host, port));

            List<SocketAddress> socketAddressList = new ArrayList<>();
            socketAddressList.add(new InetSocketAddress(host, port));
            addressList.add(new EquivalentAddressGroup(socketAddressList));
        });

        if (!addressList.isEmpty()) {
            listener.onAddresses(addressList, Attributes.EMPTY);
        }
    }
}

// Node: repos/cloned_ms_repos/saigonparking/common/src/main/java/com/bht/saigonparking/common/loadbalance/SaigonParkingNameResolver.java:SaigonParkingNameResolver.<init>
