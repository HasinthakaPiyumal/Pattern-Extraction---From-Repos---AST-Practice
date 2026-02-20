// Cluster 28

package edu.fudan.common.entity;

import java.io.Serializable;

/**
 * @author fdse
 */
public enum Type implements Serializable{
    /**
     * G
     */
    G("G", 1),
    /**
     * D
     */
    D("D", 2),
    /**
     * Z
     */
    Z("Z",3),
    /**
     * T
     */
    T("T", 4),
    /**
     * K
     */
    K("K", 5);

    private String name;
    private int index;

    Type(String name, int index) {
        this.name = name;
        this.index = index;
    }

    public static String getName(int index) {
        for (Type type : Type.values()) {
            if (type.getIndex() == index) {
                return type.name;
            }
        }
        return null;
    }

    public String getName() {
        return name;
    }

    void setName(String name) {
        this.name = name;
    }

    public int getIndex() {
        return index;
    }

    void setIndex(int index) {
        this.index = index;
    }
}


// Node: setIndex
package edu.fudan.common.entity;

import java.io.Serializable;

/**
 * @author fdse
 */
public enum AssuranceType implements Serializable{

    /**
     * traffic accident assurance
     */
    TRAFFIC_ACCIDENT (1, "Traffic Accident Assurance", 3.0);

    /**
     * index of assurance type
     */
    private  int index;
    /**
     * the assurance type name
     */
    private String name;
    /**
     * the price of this type of assurence
     */
    private double price;

     AssuranceType(int index, String name, double price){
         this.index = index;
        this.name = name;
        this.price  = price;
    }

    public int getIndex() {
        return index;
    }

    void setIndex(int index) {
        this.index = index;
    }

    public String getName() {
        return name;
    }

    void setName(String name) {
        this.name = name;
    }

    public double getPrice() {
        return price;
    }

    void setPrice(double price) {
        this.price = price;
    }

    public static AssuranceType getTypeByIndex(int index){
         AssuranceType[] ats = AssuranceType.values();
         for(AssuranceType at : ats){
             if(at.getIndex() == index){
                 return at;
             }
         }
         return null;
    }


}


package assurance.entity;

import java.io.Serializable;

/**
 * @author fdse
 */
public enum AssuranceType implements Serializable {

    /**
     * Traffic Accident Assurance
     */
    TRAFFIC_ACCIDENT(1, "Traffic Accident Assurance", 3.0);

    /**
     * index of assurance type
     */
    private int index;

    /**
     * the assurance type name
     */
    private String name;

    /**
     * the price of this type of assurence
     */
    private double price;

    AssuranceType(int index, String name, double price) {
        this.index = index;
        this.name = name;
        this.price = price;
    }

    public int getIndex() {
        return index;
    }

    void setIndex(int index) {
        this.index = index;
    }

    public String getName() {
        return name;
    }

    void setName(String name) {
        this.name = name;
    }

    public double getPrice() {
        return price;
    }

    void setPrice(double price) {
        this.price = price;
    }

    public static AssuranceType getTypeByIndex(int index) {
        AssuranceType[] ats = AssuranceType.values();
        for (AssuranceType at : ats) {
            if (at.getIndex() == index) {
                return at;
            }
        }
        return null;
    }
}


// Node: queryPriceInformation
package consignprice.controller;

import consignprice.entity.ConsignPrice;
import consignprice.service.ConsignPriceService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.*;

import static org.springframework.http.ResponseEntity.ok;

/**
 * @author fdse
 */
@RestController
@RequestMapping("/api/v1/consignpriceservice")
public class ConsignPriceController {

    @Autowired
    ConsignPriceService service;

    private static final Logger logger = LoggerFactory.getLogger(ConsignPriceController.class);

    @GetMapping(path = "/welcome")
    public String home(@RequestHeader HttpHeaders headers) {
        return "Welcome to [ ConsignPrice Service ] !";
    }

    @GetMapping(value = "/consignprice/{weight}/{isWithinRegion}")
    public HttpEntity getPriceByWeightAndRegion(@PathVariable String weight, @PathVariable String isWithinRegion,
                                                @RequestHeader HttpHeaders headers) {
        logger.info("[getPriceByWeightAndRegion][Get price by weight and region][weight: {}, region: {}]", weight, isWithinRegion);
        return ok(service.getPriceByWeightAndRegion(Double.parseDouble(weight),
                Boolean.parseBoolean(isWithinRegion), headers));
    }

    @GetMapping(value = "/consignprice/price")
    public HttpEntity getPriceInfo(@RequestHeader HttpHeaders headers) {
        logger.info("[getPriceInfo][Get price info]");
        return ok(service.queryPriceInformation(headers));
    }

    @GetMapping(value = "/consignprice/config")
    public HttpEntity getPriceConfig(@RequestHeader HttpHeaders headers) {
        logger.info("[getPriceConfig][Get price config]");
        return ok(service.getPriceConfig(headers));
    }

    @PostMapping(value = "/consignprice")
    public HttpEntity modifyPriceConfig(@RequestBody ConsignPrice priceConfig,
                                        @RequestHeader HttpHeaders headers) {
        logger.info("[modifyPriceConfig][Create and modify price][config: {}]", priceConfig);
        return ok(service.createAndModifyPrice(priceConfig, headers));
    }
}


// Node: getPriceConfig
// Node: modifyPriceConfig
// Node: createAndModifyPrice
package consignprice.service;

import consignprice.entity.ConsignPrice;
import edu.fudan.common.util.Response;
import org.springframework.http.HttpHeaders;

/**
 * @author fdse
 */
public interface ConsignPriceService {

    /**
     * get price by weight and region
     *
     * @param weight weight
     * @param isWithinRegion whether is within region
     * @param headers headers
     * @return Response
     */
    Response getPriceByWeightAndRegion(double weight, boolean isWithinRegion, HttpHeaders headers);

    /**
     * query price information
     *
     * @param headers headers
     * @return Response
     */
    Response queryPriceInformation(HttpHeaders headers);

    /**
     * create and modify price
     *
     * @param config config
     * @param headers headers
     * @return Response
     */
    Response createAndModifyPrice(ConsignPrice config, HttpHeaders headers);

    /**
     * get price config
     *
     * @param headers headers
     * @return Response
     */
    Response getPriceConfig(HttpHeaders headers);
}


// Node: repos/cloned_ms_repos/train-ticket/ts-consign-price-service/src/main/java/consignprice/service/ConsignPriceService.java:ConsignPriceService.<init>
package consignprice.service;

import consignprice.entity.ConsignPrice;
import consignprice.repository.ConsignPriceConfigRepository;
import edu.fudan.common.util.Response;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpHeaders;
import org.springframework.stereotype.Service;

/**
 * @author fdse
 */
@Service
public class ConsignPriceServiceImpl implements ConsignPriceService {

    @Autowired
    private ConsignPriceConfigRepository repository;

    String success = "Success";

    private static final Logger LOGGER = LoggerFactory.getLogger(ConsignPriceServiceImpl.class);

    @Override
    public Response getPriceByWeightAndRegion(double weight, boolean isWithinRegion, HttpHeaders headers) {
        ConsignPrice priceConfig = repository.findByIndex(0);
        double price = 0;
        double initialPrice = priceConfig.getInitialPrice();
        if (weight <= priceConfig.getInitialWeight()) {
            price = initialPrice;
        } else {
            double extraWeight = weight - priceConfig.getInitialWeight();
            if (isWithinRegion) {
                price = initialPrice + extraWeight * priceConfig.getWithinPrice();
            }else {
                price = initialPrice + extraWeight * priceConfig.getBeyondPrice();
            }
        }
        return new Response<>(1, success, price);
    }

    @Override
    public Response queryPriceInformation(HttpHeaders headers) {
        StringBuilder sb = new StringBuilder();
        ConsignPrice price = repository.findByIndex(0);
        sb.append("The price of weight within ");
        sb.append(price.getInitialWeight());
        sb.append(" is ");
        sb.append(price.getInitialPrice());
        sb.append(". The price of extra weight within the region is ");
        sb.append(price.getWithinPrice());
        sb.append(" and beyond the region is ");
        sb.append(price.getBeyondPrice());
        sb.append("\n");
        return new Response<>(1, success, sb.toString());
    }

    @Override
    public Response createAndModifyPrice(ConsignPrice config, HttpHeaders headers) {
        ConsignPriceServiceImpl.LOGGER.info("[createAndModifyPrice][Create New Price Config]");
        //update price
        ConsignPrice originalConfig;
        if (repository.findByIndex(0) != null) {
            originalConfig = repository.findByIndex(0);
        } else {
            originalConfig = new ConsignPrice();
        }
        originalConfig.setId(config.getId());
        originalConfig.setIndex(0);
        originalConfig.setInitialPrice(config.getInitialPrice());
        originalConfig.setInitialWeight(config.getInitialWeight());
        originalConfig.setWithinPrice(config.getWithinPrice());
        originalConfig.setBeyondPrice(config.getBeyondPrice());
        repository.save(originalConfig);
        return new Response<>(1, success, originalConfig);
    }

    @Override
    public Response getPriceConfig(HttpHeaders headers) {
        return new Response<>(1, success, repository.findByIndex(0));
    }
}


// Node: getInitialPrice
// Node: getInitialWeight
// Node: getWithinPrice
// Node: getBeyondPrice
// Node: setInitialPrice
// Node: setInitialWeight
// Node: setWithinPrice
// Node: setBeyondPrice
package consignprice.init;

import consignprice.entity.ConsignPrice;
import consignprice.service.ConsignPriceService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

import java.util.UUID;

/**
 * @author fdse
 */
@Component
public class InitData implements CommandLineRunner {
    @Autowired
    ConsignPriceService service;

    private static final Logger LOGGER = LoggerFactory.getLogger(InitData.class);

    @Override
    public void run(String... strings) throws Exception {
        InitData.LOGGER.info("[InitData.run][Consign price service][Init data operation]");
        ConsignPrice config = new ConsignPrice();
        config.setId(UUID.randomUUID().toString());
        config.setIndex(0);
        config.setInitialPrice(8);
        config.setInitialWeight(1);
        config.setWithinPrice(2);
        config.setBeyondPrice(4);

        service.createAndModifyPrice(config, null);
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-consign-price-service/src/main/java/consignprice/init/InitData.java:InitData.<init>
package inside_payment.entity;

import java.io.Serializable;

/**
 * @author fdse
 */
public enum MoneyType implements Serializable {

    /**
     * add money
     */
    A("Add Money",1),
    /**
     * draw back money
     */
    D("Draw Back Money",2);

    private String name;
    private int index;

    MoneyType(String name, int index) {
        this.name = name;
        this.index = index;
    }

    public static String getName(int index) {
        for (MoneyType type : MoneyType.values()) {
            if (type.getIndex() == index) {
                return type.name;
            }
        }
        return null;
    }

    public String getName() {
        return name;
    }

    void setName(String name) {
        this.name = name;
    }

    public int getIndex() {
        return index;
    }

    void setIndex(int index) {
        this.index = index;
    }
}


package inside_payment.entity;

import java.io.Serializable;

/**
 * @author fdse
 */
public enum  PaymentType implements Serializable {

    /**
     * payment
     */
    P("Payment",1),
    /**
     * difference
     */
    D("Difference",2),
    /**
     * outside payment
     */
    O("Outside Payment",3),
    /**
     * difference and outside payment
     */
    E("Difference & Outside Payment",4);

    private String name;
    private int index;

    PaymentType(String name, int index) {
        this.name = name;
        this.index = index;
    }

    public static String getName(int index) {
        for (PaymentType type : PaymentType.values()) {
            if (type.getIndex() == index) {
                return type.name;
            }
        }
        return null;
    }

    public String getName() {
        return name;
    }

    void setName(String name) {
        this.name = name;
    }

    public int getIndex() {
        return index;
    }

    void setIndex(int index) {
        this.index = index;
    }
}


