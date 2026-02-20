// Cluster 13

package com.bht.saigonparking.common.base;

import java.io.IOException;

import javax.annotation.PostConstruct;
import javax.annotation.PreDestroy;

/**
 * Saigon Parking Project Base Bean
 *
 * @author bht
 */
public interface BaseBean {

    /**
     * This method will be called
     * as the bean has been initialized
     */
    @PostConstruct
    default void initialize() throws IOException {
    }

    /**
     * This method will be called
     * as the bean is about to be destroyed
     */
    @PreDestroy
    default void destroy() {
    }
}

// Node: destroy
package com.bht.saigonparking.common.spring;

import java.io.IOException;
import java.lang.reflect.Proxy;

import org.apache.logging.log4j.Level;
import org.springframework.beans.factory.config.DestructionAwareBeanPostProcessor;
import org.springframework.lang.NonNull;

import com.bht.saigonparking.common.base.BaseBean;
import com.bht.saigonparking.common.util.LoggingUtil;

import lombok.AllArgsConstructor;


/**
 *
 * Hook into the life cycle of each spring bean (create, destroy,...)
 *
 * @author bht
 */
@AllArgsConstructor
public final class SpringBeanLifeCycle implements BaseBean, DestructionAwareBeanPostProcessor {

    private final String moduleBasePackage;

    @Override
    public void initialize() throws IOException {
        BaseBean.super.initialize();
        LoggingUtil.log(Level.INFO, "SPRING", "BeanCreation", "springBeanLifeCycle");
    }


    @Override
    public void destroy() {
        BaseBean.super.destroy();
        LoggingUtil.log(Level.INFO, "SPRING", "BeanDestruction", "springBeanLifeCycle");
    }


    @Override
    public Object postProcessBeforeInitialization(@NonNull Object bean, @NonNull String beanName) {
        if (!(bean instanceof Proxy) && bean.getClass().getPackage().getName().startsWith(moduleBasePackage)) {
            LoggingUtil.log(Level.INFO, "SPRING", "BeanCreation", beanName);
        }
        return DestructionAwareBeanPostProcessor.super.postProcessBeforeInitialization(bean, beanName);
    }


    @Override
    public void postProcessBeforeDestruction(@NonNull Object bean, @NonNull String beanName) {
        if (!(bean instanceof Proxy) && bean.getClass().getPackage().getName().startsWith(moduleBasePackage)) {
            LoggingUtil.log(Level.INFO, "SPRING", "BeanDestruction", beanName);
        }
    }
}

package com.bht.saigonparking.emulator.configuration;

import java.lang.reflect.Proxy;

import org.apache.logging.log4j.Level;
import org.springframework.beans.factory.config.DestructionAwareBeanPostProcessor;
import org.springframework.lang.NonNull;
import org.springframework.stereotype.Component;

import com.bht.saigonparking.emulator.base.BaseBean;
import com.bht.saigonparking.emulator.util.LoggingUtil;

/**
 *
 * @author bht
 */
@Component
public final class SpringBeanLifeCycle implements BaseBean, DestructionAwareBeanPostProcessor {


    @Override
    public void initialize() {
        BaseBean.super.initialize();
        LoggingUtil.log(Level.INFO, "SPRING", "BeanCreation", "springBeanLifeCycle");
    }


    @Override
    public void destroy() {
        BaseBean.super.destroy();
        LoggingUtil.log(Level.INFO, "SPRING", "BeanDestruction", "springBeanLifeCycle");
    }


    @Override
    public Object postProcessBeforeInitialization(@NonNull Object bean, @NonNull String beanName) {
        if (!(bean instanceof Proxy) && bean.getClass().getPackage().getName().startsWith(AppConfiguration.BASE_PACKAGE_SERVER)) {
            LoggingUtil.log(Level.INFO, "SPRING", "BeanCreation", beanName);
        }
        return DestructionAwareBeanPostProcessor.super.postProcessBeforeInitialization(bean, beanName);
    }


    @Override
    public void postProcessBeforeDestruction(@NonNull Object bean, @NonNull String beanName) {
        if (!(bean instanceof Proxy) && bean.getClass().getPackage().getName().startsWith(AppConfiguration.BASE_PACKAGE_SERVER)) {
            LoggingUtil.log(Level.INFO, "SPRING", "BeanDestruction", beanName);
        }
    }
}

package com.bht.saigonparking.emulator.base;

import javax.annotation.PostConstruct;
import javax.annotation.PreDestroy;

/**
 *
 * @author bht
 */
public interface BaseBean {


    @PostConstruct
    default void initialize() {
    }

    @PreDestroy
    default void destroy() {
    }
}

