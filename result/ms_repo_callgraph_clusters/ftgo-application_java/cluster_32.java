// Cluster 32

package net.chrisrichardson.ftgo.restaurantservice.events;

import net.chrisrichardson.ftgo.common.Address;
import net.chrisrichardson.ftgo.restaurantservice.domain.RestaurantMenu;

public class RestaurantCreated implements RestaurantDomainEvent {
  private String name;
  private Address address;
  private RestaurantMenu menu;

  public String getName() {
    return name;
  }

  private RestaurantCreated() {
  }

  public RestaurantCreated(String name, Address address, RestaurantMenu menu) {
    this.name = name;
    this.address = address;
    this.menu = menu;

    if (menu == null) 
      throw new NullPointerException("Null Menu");
    if (address == null) 
      throw new NullPointerException("Null address");
  }

  public RestaurantMenu getMenu() {
    return menu;
  }

  public void setMenu(RestaurantMenu menu) {
    this.menu = menu;
  }

  public void setName(String name) {
    this.name = name;
  }

  public Address getAddress() {
    return address;
  }

  public void setAddress(Address address) {
    this.address = address;
  }
}


// Node: setMenu
package net.chrisrichardson.ftgo.restaurantservice.domain;

import net.chrisrichardson.ftgo.common.Address;

public class CreateRestaurantRequest {

  private String name;
  private Address address;
  private RestaurantMenu menu;

  private CreateRestaurantRequest() {

  }

  public CreateRestaurantRequest(String name, Address address, RestaurantMenu menu) {
    this.name = name;
    this.address = address;
    this.menu = menu;
  }

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  public RestaurantMenu getMenu() {
    return menu;
  }

  public void setMenu(RestaurantMenu menu) {
    this.menu = menu;
  }

  public Address getAddress() {
    return address;
  }
}


package net.chrisrichardson.ftgo.restaurantservice.events;

import net.chrisrichardson.ftgo.common.Address;
import net.chrisrichardson.ftgo.restaurantservice.domain.RestaurantMenu;

public class RestaurantCreated implements RestaurantDomainEvent {
  private String name;
  private Address address;
  private RestaurantMenu menu;

  public String getName() {
    return name;
  }

  private RestaurantCreated() {
  }

  public RestaurantCreated(String name, Address address, RestaurantMenu menu) {
    this.name = name;
    this.address = address;
    this.menu = menu;


    if (menu == null) 
      throw new NullPointerException("Null Menu");
    if (address == null) 
      throw new NullPointerException("Null address");    
  }

  public RestaurantMenu getMenu() {
    return menu;
  }

  public void setMenu(RestaurantMenu menu) {
    this.menu = menu;
  }

  public void setName(String name) {
    this.name = name;
  }

  public Address getAddress() {
    return address;
  }

  public void setAddress(Address address) {
    this.address = address;
  }
}


package net.chrisrichardson.ftgo.restaurantservice.domain;

import net.chrisrichardson.ftgo.common.Address;

public class CreateRestaurantRequest {

  private String name;
  private Address address;
  private RestaurantMenu menu;

  private CreateRestaurantRequest() {

  }

  public CreateRestaurantRequest(String name, Address address, RestaurantMenu menu) {
    this.name = name;
    this.address = address;
    this.menu = menu;
  }

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  public RestaurantMenu getMenu() {
    return menu;
  }

  public void setMenu(RestaurantMenu menu) {
    this.menu = menu;
  }

  public Address getAddress() {
    return address;
  }
}


